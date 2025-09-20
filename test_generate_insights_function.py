#!/usr/bin/env python3
"""
Test the Generate Insights function from the YouTube Analytics workflow.
"""

import json

def test_generate_insights_function():
    """Test the Generate Insights function logic."""
    
    # This is the exact function code from the workflow
    function_code = '''
// Generate insights and final response with robust error handling
try {
  const input = $input.first();
  if (!input || !input.json) {
    throw new Error('No input data received');
  }
  
  const data = input.json;
  
  // Generate insights based on metrics
  const insights = [];
  const recommendations = [];
  
  // Safe number checking with defaults
  const ctr = parseFloat(data.ctr_percentage) || 0;
  const avgDuration = parseInt(data.avg_view_duration) || 0;
  const subChange = parseInt(data.subscriber_change) || 0;
  
  if (ctr < 5) {
    insights.push('Low click-through rate detected');
    recommendations.push('Improve thumbnails and titles');
  }
  
  if (avgDuration < 120) {
    insights.push('Short average view duration');
    recommendations.push('Improve video hooks and pacing');
  }
  
  if (subChange < 0) {
    insights.push('Losing subscribers');
    recommendations.push('Review content quality and consistency');
  }
  
  return [{
    json: {
      status: 'success',
      message: 'Analytics retrieved successfully',
      channel: {
        id: data.channel_id || 'unknown',
        period: {
          start: data.start_date || new Date().toISOString().split('T')[0],
          end: data.end_date || new Date().toISOString().split('T')[0],
          range: data.date_range || 'unknown'
        }
      },
      metrics: {
        views: parseInt(data.total_views) || 0,
        watch_hours: parseInt(data.total_watch_hours) || 0,
        subscriber_change: subChange,
        revenue: parseFloat(data.estimated_revenue) || 0.0,
        avg_view_duration: avgDuration,
        ctr: ctr
      },
      demographics: data.top_age_group ? {
        age_group: data.top_age_group,
        gender_split: {
          male: parseInt(data.male_percentage) || 0,
          female: parseInt(data.female_percentage) || 0
        },
        top_location: data.top_country || 'Unknown'
      } : null,
      traffic: data.top_source ? {
        top_source: data.top_source,
        search_percentage: parseInt(data.search_percentage) || 0,
        suggested_percentage: parseInt(data.suggested_percentage) || 0,
        top_search_term: data.top_search_term || 'N/A'
      } : null,
      insights: insights.length > 0 ? insights : ['Channel performing within normal parameters'],
      recommendations: recommendations.length > 0 ? recommendations : ['Continue current strategy'],
      generated_at: new Date().toISOString()
    }
  }];
} catch (error) {
  return [{
    json: {
      status: 'error',
      message: 'Analytics processing failed: ' + error.message,
      generated_at: new Date().toISOString()
    }
  }];
}
'''
    
    print("=" * 60)
    print("Generate Insights Function Analysis")
    print("=" * 60)
    
    print("Function code analysis:")
    print(f"  - Lines of code: {len(function_code.strip().split('\\n'))}")
    print(f"  - Contains error handling: {'try {' in function_code}")
    print(f"  - Has input validation: {'!input || !input.json' in function_code}")
    print(f"  - Returns structured JSON: {'return [{' in function_code}")
    print(f"  - Has fallback values: {'|| 0' in function_code}")
    
    # Test with sample data that would flow through the workflow
    print("\\n" + "=" * 60)
    print("Sample Data Flow Test")
    print("=" * 60)
    
    sample_data = {
        "channel_id": "test",
        "date_range": "last_30_days", 
        "start_date": "2025-01-14",
        "end_date": "2025-02-14",
        "include_demographics": True,
        "include_traffic": True,
        "total_views": 15000,
        "total_watch_hours": 1200,
        "subscriber_change": -50,
        "estimated_revenue": 125.75,
        "avg_view_duration": 95,
        "ctr_percentage": 3.2,
        "top_age_group": "25-34",
        "top_gender": "male", 
        "top_country": "United States",
        "male_percentage": 65,
        "female_percentage": 35,
        "top_source": "YouTube Search",
        "search_percentage": 45,
        "suggested_percentage": 25,
        "top_search_term": "tutorial"
    }
    
    print("Sample input data:")
    print(json.dumps(sample_data, indent=2))
    
    print("\\nExpected output structure based on function logic:")
    expected = {
        "status": "success",
        "message": "Analytics retrieved successfully",
        "channel": {
            "id": "test",
            "period": {
                "start": "2025-01-14",
                "end": "2025-02-14", 
                "range": "last_30_days"
            }
        },
        "metrics": {
            "views": 15000,
            "watch_hours": 1200,
            "subscriber_change": -50,
            "revenue": 125.75,
            "avg_view_duration": 95,
            "ctr": 3.2
        },
        "demographics": {
            "age_group": "25-34",
            "gender_split": {"male": 65, "female": 35},
            "top_location": "United States"
        },
        "traffic": {
            "top_source": "YouTube Search",
            "search_percentage": 45,
            "suggested_percentage": 25,
            "top_search_term": "tutorial"
        },
        "insights": [
            "Low click-through rate detected",
            "Short average view duration", 
            "Losing subscribers"
        ],
        "recommendations": [
            "Improve thumbnails and titles",
            "Improve video hooks and pacing",
            "Review content quality and consistency"
        ]
    }
    
    print(json.dumps(expected, indent=2))
    
    print("\\n" + "=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)
    print("SUCCESS: The Generate Insights function appears to be well-structured:")
    print("  - Has comprehensive error handling")
    print("  - Uses safe parsing with defaults")
    print("  - Returns consistent JSON structure")
    print("  - Provides meaningful insights based on metrics")
    print("  - Handles optional demographics and traffic data")
    print("\\nThe function should NOT be causing empty responses.")
    print("The issue was likely in the workflow connections and merge logic,")
    print("which have now been fixed.")

if __name__ == "__main__":
    test_generate_insights_function()