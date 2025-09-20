#!/usr/bin/env python3
"""
Debug the workflow execution by analyzing the conditional logic
and potential data loss points in the YouTube Analytics workflow.
"""

import json
import requests
import time

def analyze_workflow_logic():
    """Analyze the workflow for potential execution issues"""
    
    with open('workflows/youtube_analytics_PRODUCTION.json', 'r') as f:
        workflow = json.load(f)
    
    nodes = {node['id']: node for node in workflow['nodes']}
    connections = workflow['connections']
    
    print("=== WORKFLOW EXECUTION ANALYSIS ===")
    
    # Check conditional nodes that could cause branching issues
    conditional_nodes = []
    for node_id, node in nodes.items():
        if node['type'] == 'n8n-nodes-base.if':
            conditional_nodes.append(node)
            print(f"\nConditional node: {node['name']} ({node_id})")
            
            # Check the condition
            conditions = node['parameters'].get('conditions', {})
            print(f"  Conditions: {json.dumps(conditions, indent=2)}")
            
            # Check what happens on true/false paths
            if node_id in connections:
                main_conns = connections[node_id]['main']
                print(f"  True path: {main_conns[0][0]['node'] if main_conns[0] else 'None'}")
                print(f"  False path: {main_conns[1][0]['node'] if len(main_conns) > 1 and main_conns[1] else 'None'}")
    
    # Check merge nodes
    print(f"\n=== MERGE NODES ===")
    for node_id, node in nodes.items():
        if node['type'] == 'n8n-nodes-base.merge':
            print(f"\nMerge node: {node['name']} ({node_id})")
            params = node['parameters']
            print(f"  Mode: {params.get('mode', 'default')}")
            print(f"  Combination mode: {params.get('combinationMode', 'default')}")
            
    # Check function node
    function_node = nodes.get('generate_insights')
    if function_node:
        print(f"\n=== FUNCTION NODE ANALYSIS ===")
        func_code = function_node['parameters']['functionCode']
        print(f"Function code length: {len(func_code)} characters")
        
        # Check for common issues
        issues = []
        if 'return' not in func_code:
            issues.append("No return statement found")
        if '$input' not in func_code:
            issues.append("Not accessing input data")
        if 'json:' not in func_code:
            issues.append("Not returning JSON structure")
            
        if issues:
            print("Potential issues:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("Function code looks structurally correct")
    
    # Test the conditional logic with sample data
    print(f"\n=== TESTING CONDITIONAL LOGIC ===")
    
    test_data = {
        'channel_id': 'test',
        'include_demographics': True,
        'include_traffic': True  # Note: this should match the field name in workflow
    }
    
    # Test demographics condition
    demo_condition = test_data.get('include_demographics', False) 
    print(f"Demographics condition result: {demo_condition}")
    
    # Test traffic condition  
    traffic_condition = test_data.get('include_traffic', False)
    print(f"Traffic condition result: {traffic_condition}")
    
    # Check if the field names match
    print(f"\nField name analysis:")
    print(f"  Test data has 'include_traffic': {'include_traffic' in test_data}")
    print(f"  Workflow expects 'include_traffic': checking...")
    
    # Check the actual field name used in Check Traffic node
    check_traffic_node = nodes.get('check_traffic')
    if check_traffic_node:
        condition = check_traffic_node['parameters']['conditions']['boolean'][0]
        field_name = condition['value1']
        print(f"  Workflow checks: {field_name}")
        
        # Test the actual expression
        if "include_traffic" in field_name:
            print("  Field name matches!")
        else:
            print(f"  MISMATCH! Workflow expects different field name")

def simulate_workflow_execution():
    """Simulate the workflow execution step by step"""
    
    print(f"\n=== WORKFLOW EXECUTION SIMULATION ===")
    
    # Starting payload
    payload = {'channel_id': 'test'}
    print(f"1. Webhook receives: {payload}")
    
    # Prepare Parameters step
    prepared = {
        'channel_id': payload.get('channel_id', 'UC_default'),
        'date_range': payload.get('date_range', 'last_30_days'),
        'start_date': '2024-08-15',  # Mock date
        'end_date': '2024-09-14',
        'include_demographics': payload.get('include_demographics') is not False,  # True by default
        'include_traffic': payload.get('include_traffic_sources') is not False      # True by default
    }
    print(f"2. Prepare Parameters result: {prepared}")
    
    # Mock Metrics step
    mock_metrics = {
        **prepared,
        'total_views': 50000,
        'total_watch_hours': 2500,
        'subscriber_change': 100,
        'estimated_revenue': 500.00,
        'avg_view_duration': 180,
        'ctr_percentage': 7.5
    }
    print(f"3. Mock Metrics result: {mock_metrics}")
    
    # Demographics check
    demo_check = mock_metrics['include_demographics']
    print(f"4. Demographics check: {demo_check}")
    
    if demo_check:
        demographics_data = {
            **mock_metrics,
            'top_age_group': '25-34',
            'top_gender': 'male',
            'top_country': 'United States',
            'male_percentage': 60,
            'female_percentage': 35
        }
        print(f"5a. Demographics added: {list(demographics_data.keys())}")
    else:
        demographics_data = {
            **mock_metrics,
            'demographics': 'not_included'
        }
        print(f"5b. No demographics: {list(demographics_data.keys())}")
    
    # Traffic check
    traffic_check = demographics_data['include_traffic']
    print(f"6. Traffic check: {traffic_check}")
    
    if traffic_check:
        final_data = {
            **demographics_data,
            'top_source': 'YouTube Search',
            'top_search_term': 'tutorial',
            'search_percentage': 45,
            'suggested_percentage': 25
        }
        print(f"7a. Traffic added: {list(final_data.keys())}")
    else:
        final_data = {
            **demographics_data,
            'traffic_sources': 'not_included'
        }
        print(f"7b. No traffic: {list(final_data.keys())}")
    
    print(f"\n8. Final data passed to Generate Insights:")
    print(f"   Keys: {list(final_data.keys())}")
    print(f"   Sample values: channel_id={final_data['channel_id']}, views={final_data['total_views']}")

if __name__ == "__main__":
    analyze_workflow_logic()
    simulate_workflow_execution()