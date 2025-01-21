from typing import List
import pandas as pd
from sfn_blueprint import SFNAgent
from sfn_blueprint import Task
from sfn_blueprint import SFNAIHandler
import os
from sfn_blueprint import SFNPromptManager
from mapping_agent.config.model_config import MODEL_CONFIG, DEFAULT_LLM_MODEL, DEFAULT_LLM_PROVIDER

class SFNCategoryIdentificationAgent(SFNAgent):
    def __init__(self, llm_provider='openai'):
        super().__init__(name="Category Identification", role="Data Categorizer")
        self.ai_handler = SFNAIHandler()
        self.llm_provider = llm_provider
        self.model_config = MODEL_CONFIG["category_identifier"]
        parent_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
        prompt_config_path = os.path.join(parent_path, 'config', 'prompt_config.json')
        self.prompt_manager = SFNPromptManager(prompt_config_path)
    
    def execute_task(self, task: Task) -> str:
        """
        Execute the category identification task.
        
        :param task: Task object containing the DataFrame to be categorized
        :return: Identified category as a string
        """
        if not isinstance(task.data, pd.DataFrame):
            raise ValueError("Task data must be a pandas DataFrame")

        columns = task.data.columns.tolist()
        category = self._identify_category(columns)
        return category

    def _identify_category(self, columns: List[str]) -> str:
        """
        Identify the category of the data based on the column names.
        
        :param columns: List of column names in the dataset
        :return: Identified category as a string
        """
        # Get prompts using PromptManager
        system_prompt, user_prompt = self.prompt_manager.get_prompt(
            agent_type='category_identifier', 
            llm_provider=self.llm_provider,
            prompt_type='main',
            columns=columns
        )
        
        # Get provider config or use default if not found
        provider_config = self.model_config.get(self.llm_provider, {
            "model": DEFAULT_LLM_MODEL,
            "temperature": 0.5,
            "max_tokens": 500,
            "n": 1,
            "stop": None
        })
        
        # Prepare the configuration for the API call
        configuration = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": provider_config["temperature"],
            "max_tokens": provider_config["max_tokens"],
            "n": provider_config["n"],
            "stop": provider_config["stop"]
        }

        # Use the AI handler to route the request
        response, token_cost_summary = self.ai_handler.route_to(
            llm_provider=self.llm_provider,
            configuration=configuration,
            model=provider_config['model']
        )

        # Handle response based on provider
        if isinstance(response, dict):  # For Cortex
            category = response['choices'][0]['message']['content']
        elif hasattr(response, 'choices'):  # For OpenAI
            category = response.choices[0].message.content
        else:  # For other providers or direct string response
            category = response
        
        return self._normalize_category(category.strip().lower())

    def _normalize_category(self, category: str) -> str:
        """
        Normalize the category returned by the OpenAI model to match expected categories.
        
        :param category: Category string returned by the model
        :return: Normalized category string
        """
        valid_categories = ["billing", "usage", "support", "other"]
        
        for valid_category in valid_categories:
            if valid_category in category:
                return valid_category
        
        return "none of these"

    def get_validation_params(self, response, task):
        """
        Get parameters for validation
        :param response: The response from execute_task to validate (category)
        :param task: The validation task containing the DataFrame
        :return: Dictionary with validation parameters
        """
        if not isinstance(task.data, pd.DataFrame):
            raise ValueError("Task data must be a pandas DataFrame")

        # Get validation prompts from prompt manager
        prompts = self.prompt_manager.get_prompt(
            agent_type='category_identifier',
            llm_provider=self.llm_provider,
            prompt_type='validation',
            actual_output=response,
            columns=task.data.columns.tolist()
        )
        return prompts