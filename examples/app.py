import sys
import os
import streamlit as st
from sfn_blueprint import SFNAgent, Task, SFNSessionManager
from sfn_blueprint import SFNDataLoader, setup_logger, SFNDataPostProcessor
from mapping_agent.agents.category_identification_agent import SFNCategoryIdentificationAgent
from mapping_agent.agents.column_mapping_agent import SFNColumnMappingAgent
from mapping_agent.views.streamlit_views import StreamlitView
from sfn_blueprint import SFNValidateAndRetryAgent
from mapping_agent.config.model_config import DEFAULT_LLM_PROVIDER


def run_app():
    # Initialize view and session
    view = StreamlitView(title="Column Mapping App")
    session = SFNSessionManager()
    
    col1, col2 = view.create_columns([7, 1])
    with col1:
        view.display_title()
    with col2:
        if view.display_button("🔄", key="reset_button"):
            session.clear()
            view.rerun_script()

    # Setup logger
    logger, handler = setup_logger()
    logger.info('Starting Column Mapping App')

    # Step 1: Data Loading and Preview
    view.display_header("Step 1: Data Loading and Preview")
    view.display_markdown("---")
    
    uploaded_file = view.file_uploader("Choose a CSV or Excel file", accepted_types=["csv", "xlsx", "json", "parquet"])

    if uploaded_file is not None:
        if session.get('df') is None:
            with view.display_spinner('Loading data...'):
                try:
                    data_loader = SFNDataLoader()
                    
                    # Save the uploaded file temporarily and get its path
                    file_path = view.save_uploaded_file(uploaded_file)
                    logger.info(f'Started loading saved file: {file_path}')
                    
                    # Create task with file path
                    load_task = Task("Load the uploaded file", data=uploaded_file, path=file_path)
                    logger.info('Loading task... now executing task')
                    
                    df = data_loader.execute_task(load_task)
                    logger.info('Task execution done...')

                    # Delete temp file after processing
                    if df is not None:
                        view.delete_uploaded_file(file_path)

                    session.set('df', df)
                    logger.info(f"Data loaded successfully. Shape: {df.shape}")
                    view.show_message(f"✅ Data loaded successfully. Shape: {df.shape}", "success")
                    
                    view.display_subheader("Data Preview")
                    view.display_dataframe(df.head())
                    
                except Exception as e:
                    logger.error(f"Error loading file: {e}")
                    view.show_message(f"❌ Error loading file: {str(e)}", "error")

        # Step 2: Category Identification
        view.display_header("Step 2: Category Identification")
        view.display_markdown("---")

        if not session.get('category_identified'):
            df = session.get('df')
            category_agent = SFNCategoryIdentificationAgent()
            category_task = Task("Identify category", data=df)
            
            validation_task = Task("Validate category identification", data=df)
            
            validate_and_retry_agent = SFNValidateAndRetryAgent(
                llm_provider=DEFAULT_LLM_PROVIDER,
                for_agent='category_identification'
            )
            
            try:
                with view.display_spinner('🤖 AI is analyzing your data to identify the category...'):
                    identified_category, validation_message, is_valid = validate_and_retry_agent.complete(
                        agent_to_validate=category_agent,
                        task=category_task,
                        validation_task=validation_task,
                        method_name='execute_task',
                        get_validation_params='get_validation_params',
                        max_retries=2,
                        retry_delay=3.0
                    )
                
                if is_valid:
                    session.set('identified_category', identified_category)
                    session.set('category_identified', True)
                    logger.info(f"Category identified: {identified_category}")
                else:
                    view.show_message("❌ AI couldn't generate a valid category suggestion.", "error")
                    category_choices = ['billing', 'support', 'usage']
                    user_choice = view.radio_select(
                        "Please select the category:",
                        ["Select an option"] + category_choices,
                        key="manual_category_selection"
                    )
                    
                    if user_choice != "Select an option":
                        session.set('category', user_choice)
                        session.set('category_identified', True)
                        session.set('category_confirmed', True)
                        logger.info(f"Category manually selected: {user_choice}")
                        view.rerun_script()
                    else:
                        view.stop_execution()
            except Exception as e:
                logger.error(f"Error in category identification: {e}")
                view.show_message("❌ An error occurred during category identification.", "error")
                view.stop_execution()

        if session.get('category_identified') and not session.get('category_confirmed'):
            view.show_message(f"🎯 AI suggested category: **{session.get('identified_category')}**", "info")
            
            correct_category = view.radio_select(
                "Is this correct?",
                ["Select an option", "Yes", "No"],
                key="category_confirmation"
            )

            if correct_category == "Yes":
                if view.display_button("Confirm AI Suggestion"):
                    session.set('category', session.get('identified_category'))
                    session.set('category_confirmed', True)
                    logger.info(f"Category confirmed: {session.get('category')}")
                    view.rerun_script()

            elif correct_category == "No":
                session.set('show_category_selection', True)
                category_choices = ['billing', 'support', 'usage']
                user_choice = view.radio_select("Please select the correct category:", category_choices)
                
                if view.display_button("Confirm Selected Category"):
                    session.set('category', user_choice)
                    session.set('category_confirmed', True)
                    logger.info(f"Category confirmed: {session.get('category')}")
                    view.rerun_script()

            if not session.get('category_confirmed'):
                view.stop_execution()

        if session.get('category_confirmed'):
            view.show_message(f"✅ Category confirmed: **{session.get('category')}**", "success")

        # Step 3: Column Mapping
        if session.get('category_confirmed'):
            view.display_header("Step 3: Column Mapping")
            view.display_markdown("---")

            # First attempt at AI mapping if not done yet
            if session.get('column_mapping') is None:
                with view.display_spinner('🤖 AI is generating column mappings...'):
                    mapping_agent = SFNColumnMappingAgent()
                    mapping_task = Task("Map columns", data={
                        'dataframe': session.get('df'),
                        'category': session.get('category')
                    })
                    
                    validation_task = Task("Validate column mapping", data={
                        'dataframe': session.get('df'),
                        'category': session.get('category')
                    })
                    
                    validate_and_retry_agent = SFNValidateAndRetryAgent(
                        llm_provider=DEFAULT_LLM_PROVIDER,
                        for_agent='column_mapping'
                    )
                    
                    try:
                        column_mapping, validation_message, is_valid = validate_and_retry_agent.complete(
                            agent_to_validate=mapping_agent,
                            task=mapping_task,
                            validation_task=validation_task,
                            method_name='execute_task',
                            get_validation_params='get_validation_params',
                            max_retries=2,
                            retry_delay=3.0
                        )
                        
                        # Store validation results in session
                        session.set('mapping_validation_message', validation_message)
                        session.set('mapping_is_valid', is_valid)
                        session.set('column_mapping', column_mapping)
                        session.set('mapping_mode', 'ai_suggestion')
                        
                        if is_valid:
                            logger.info("Column mapping generated successfully.")
                            view.show_message("✅ AI has generated valid column mappings.", "success")
                            
                            # Initialize selected_mappings with AI's suggestions
                            if session.get('selected_mappings') is None:
                                session.set('selected_mappings', column_mapping)
                            
                        else:
                            view.show_message("ℹ️ AI generated mappings but they didn't meet validation criteria after multiple attempts.", "info")
                            view.show_message(validation_message, "warning")
                            view.show_message("You can proceed with manual mapping of columns.", "info")
                            
                            # Give user choice with "Select an option" as default
                            user_choice = view.radio_select(
                                "Would you like to:",
                                ["Select an option", "Map Columns Manually", "Finish"],
                                key="mapping_choice"
                            )
                            
                            if user_choice == "Map Columns Manually":
                                session.set('show_manual_mapping', True)
                                session.set('mapping_mode', 'manual')
                                view.rerun_script()  # Add this to refresh with manual mapping interface
                            elif user_choice == "Finish":
                                view.show_message("Thank you for using the Column Mapping App!", "success")
                                session.clear()
                                view.rerun_script()
                            
                            # Only stop execution if no choice is made
                            if user_choice == "Select an option":
                                view.stop_execution()

                    except Exception as e:
                        logger.error(f"Error in column mapping: {e}")
                        view.show_message("❌ An error occurred during column mapping.", "error")
                        view.show_message("You can proceed with manual mapping.", "info")
                        
                        user_choice = view.radio_select(
                            "Would you like to:",
                            ["Select an option", "Map Columns Manually", "Finish"],
                            key="mapping_choice"
                        )
                        
                        if user_choice == "Map Columns Manually":
                            session.set('show_manual_mapping', True)
                            session.set('mapping_mode', 'manual')
                            view.rerun_script()  # Add this to refresh with manual mapping interface
                        elif user_choice == "Finish":
                            view.show_message("Thank you for using the Column Mapping App!", "success")
                            session.clear()
                            view.rerun_script()
                        
                        # Only stop execution if no choice is made
                        if user_choice == "Select an option":
                            view.stop_execution()

            # Show mapping interface if we have either valid AI suggestions or manual mapping
            if session.get('mapping_mode') in ['ai_suggestion', 'manual'] and not session.get('mapping_confirmed'):
                view.display_subheader("Review Column Mappings")
                
                # Get mandatory columns for the category
                mapping_agent = SFNColumnMappingAgent()
                mandatory_columns = mapping_agent.standard_columns[session.get('category')]['mandatory']
                optional_columns = mapping_agent.standard_columns[session.get('category')]['optional']
                
                # Initialize selected_mappings if not exists
                if session.get('selected_mappings') is None:
                    # Initialize with empty mappings
                    initial_mappings = {col: None for col in mandatory_columns + optional_columns}
                    # Only apply AI suggestions if they exist and we're in AI suggestion mode
                    if session.get('column_mapping') and session.get('mapping_mode') == 'ai_suggestion':
                        initial_mappings.update(session.get('column_mapping'))
                    session.set('selected_mappings', initial_mappings)

                selected_mappings = session.get('selected_mappings')
                df_columns = session.get('df').columns.tolist()
                
                # Fix the available_input_cols calculation
                used_columns = []
                for std_col, mapped_col in selected_mappings.items():
                    if mapped_col is not None and mapped_col != "None":
                        used_columns.append(mapped_col)
                available_input_cols = [col for col in df_columns if col not in used_columns]

                # Show mandatory columns first
                view.display_subheader("Mandatory Columns")
                unmapped_mandatory = []
                for std_col in mandatory_columns:
                    col_display = f"{std_col} #"
                    current_mapping = selected_mappings.get(std_col)
                    
                    if not current_mapping:
                        unmapped_mandatory.append(std_col)
                    
                    options = ["None"] + available_input_cols
                    if current_mapping and current_mapping not in available_input_cols:
                        options = [current_mapping] + ["None"] + available_input_cols
                    
                    unique_key = f"mapping_{session.get('mapping_mode')}_{std_col}"
                    new_mapping = view.select_box(
                        f"Standard Column: **{col_display}**",
                        options=options,
                        key=unique_key
                    )
                    
                    if new_mapping == "None":
                        new_mapping = None
                    
                    if new_mapping != current_mapping:
                        selected_mappings[std_col] = new_mapping
                        session.set('selected_mappings', selected_mappings)
                        view.rerun_script()

                # Show optional columns
                view.display_subheader("Optional Columns")
                for std_col in optional_columns:
                    current_mapping = selected_mappings.get(std_col)
                    
                    # Use the same options logic as mandatory columns
                    options = ["None"] + available_input_cols
                    if current_mapping and current_mapping not in available_input_cols:
                        options = [current_mapping] + ["None"] + available_input_cols
                    
                    unique_key = f"mapping_{session.get('mapping_mode')}_{std_col}"
                    new_mapping = view.select_box(
                        f"Standard Column: **{std_col}**",
                        options=options,
                        key=unique_key
                    )
                    
                    if new_mapping == "None":
                        new_mapping = None
                    
                    if new_mapping != current_mapping:
                        selected_mappings[std_col] = new_mapping
                        session.set('selected_mappings', selected_mappings)
                        view.rerun_script()

                # Show warnings and confirm button at the bottom
                view.display_markdown("---")
                
                # Always show the confirm button
                confirm_button = view.display_button("Confirm All Mappings")
                
                if confirm_button:
                    # Check for unmapped mandatory columns when confirm is clicked
                    unmapped_mandatory = [col for col in mandatory_columns 
                                        if not selected_mappings.get(col)]
                    
                    if unmapped_mandatory:
                        # Show warning about unmapped mandatory columns
                        warning_msg = "⚠️ Cannot confirm mapping. The following mandatory columns are not mapped:\n" + \
                                    "\n".join([f"- {col}" for col in unmapped_mandatory])
                        view.show_message(warning_msg, "warning")
                        view.show_message("❗ Please map all mandatory columns before confirming.", "error")
                    else:
                        # All mandatory columns are mapped, proceed with confirmation
                        session.set('mapping_confirmed', True)
                        session.set('column_mapping', selected_mappings)
                        view.show_message("✅ All mappings confirmed", "success")
                        view.rerun_script()

            # Show mapping options if AI mapping failed and user hasn't chosen to map manually yet
            elif session.get('mapping_is_valid') is False and not session.get('mapping_confirmed'):
                view.show_message("ℹ️ AI generated mappings but they didn't meet validation criteria after multiple attempts.", "info")
                view.show_message(session.get('mapping_validation_message'), "warning")
                view.show_message("You can proceed with manual mapping of columns.", "info")
                
                # Give user choice with "Select an option" as default
                user_choice = view.radio_select(
                    "Would you like to:",
                    ["Select an option", "Map Columns Manually", "Finish"],
                    key="mapping_choice"
                )
                
                if user_choice == "Map Columns Manually":
                    session.set('show_manual_mapping', True)
                    session.set('mapping_mode', 'manual')
                    view.rerun_script()
                elif user_choice == "Finish":
                    view.show_message("Thank you for using the Column Mapping App!", "success")
                    session.clear()
                    view.rerun_script()
                elif user_choice == "Select an option":
                    view.stop_execution()

        # Step 4: Post Processing
        if session.get('mapping_confirmed'):
            selected_mappings = session.get('selected_mappings')
            standard_columns = list(selected_mappings.keys())
            # Show mapping summary before final confirmation
            mapped_cols = sum(1 for v in selected_mappings.values() if v is not None)
            total_std_cols = len(standard_columns)
            view.show_message(f"✅ {mapped_cols} Columns are mapped from Input data with Standard Columns", "success")

            view.display_header("Step 4: Post Processing")
            view.display_markdown("---")
            
            operation_type = view.radio_select(
                "Choose an operation:",
                ["View Mapped Data", "Download Mapped Data", "Finish"]
            )

            # Apply the confirmed mappings to create the final DataFrame
            if session.get('final_df') is None:
                mapped_df = session.get('df').copy()
                mapping = {v: k for k, v in session.get('selected_mappings').items() if v is not None}
                mapped_df.rename(columns=mapping, inplace=True)
                session.set('final_df', mapped_df)


            if operation_type == "View Mapped Data":
                view.display_dataframe(session.get('final_df'))
            
            elif operation_type == "Download Mapped Data":
                post_processor = SFNDataPostProcessor(session.get('final_df'))
                csv_data = post_processor.download_data('csv')
                view.create_download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name="mapped_data.csv",
                    mime_type="text/csv"
                )
            
            elif operation_type == "Finish":
                if view.display_button("Confirm Finish"):
                    view.show_message("Thank you for using the Column Mapping App!", "success")
                    session.clear()
                    view.rerun_script()
                    
if __name__ == "__main__":
    run_app()