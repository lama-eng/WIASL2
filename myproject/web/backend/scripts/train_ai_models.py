# backend/scripts/train_ai_models.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai_service import AIService
import pandas as pd
import numpy as np
from datetime import datetime
import json

def generate_training_data():
    """Generate synthetic training data for demonstration"""
    
    training_cases = [
        {
            'description': 'Emergency medical surgery needed for my child. Doctor says it\'s life-threatening and needs immediate operation. Hospital won\'t proceed without payment.',
            'urgency_score': 0.9,
            'medical_risk_score': 0.95,
            'children_present_score': 1.0,
            'sentiment_score': -0.8,
            'income_normalized': 0.2,
            'family_size_normalized': 0.4,
            'text_length_normalized': 0.6,
            'actual_priority': 98
        },
        {
            'description': 'Need help with rent for this month. Lost my job due to illness. Have two kids to support.',
            'urgency_score': 0.7,
            'medical_risk_score': 0.3,
            'children_present_score': 1.0,
            'sentiment_score': -0.6,
            'income_normalized': 0.1,
            'family_size_normalized': 0.5,
            'text_length_normalized': 0.4,
            'actual_priority': 85
        },
        {
            'description': 'Looking for assistance with school supplies for my children. Need books and uniforms for the new semester.',
            'urgency_score': 0.4,
            'medical_risk_score': 0.0,
            'children_present_score': 1.0,
            'sentiment_score': -0.2,
            'income_normalized': 0.3,
            'family_size_normalized': 0.4,
            'text_length_normalized': 0.5,
            'actual_priority': 65
        },
        {
            'description': 'Need food assistance for this month. Running low on groceries and have a family to feed.',
            'urgency_score': 0.6,
            'medical_risk_score': 0.1,
            'children_present_score': 0.8,
            'sentiment_score': -0.5,
            'income_normalized': 0.15,
            'family_size_normalized': 0.6,
            'text_length_normalized': 0.3,
            'actual_priority': 75
        },
        {
            'description': 'Single mother needing help with utility bills. Electricity about to be disconnected, have a baby at home.',
            'urgency_score': 0.8,
            'medical_risk_score': 0.2,
            'children_present_score': 1.0,
            'sentiment_score': -0.7,
            'income_normalized': 0.1,
            'family_size_normalized': 0.3,
            'text_length_normalized': 0.4,
            'actual_priority': 92
        },
        {
            'description': 'Elderly person needing assistance with medical equipment. Have chronic condition but limited income.',
            'urgency_score': 0.5,
            'medical_risk_score': 0.7,
            'children_present_score': 0.0,
            'sentiment_score': -0.4,
            'income_normalized': 0.2,
            'family_size_normalized': 0.1,
            'text_length_normalized': 0.5,
            'actual_priority': 70
        }
    ]
    
    # Generate more variations
    for i in range(20):
        base_case = training_cases[i % len(training_cases)].copy()
        
        # Add some noise
        base_case['urgency_score'] += np.random.normal(0, 0.1)
        base_case['medical_risk_score'] += np.random.normal(0, 0.1)
        base_case['children_present_score'] += np.random.normal(0, 0.1)
        base_case['sentiment_score'] += np.random.normal(0, 0.1)
        base_case['actual_priority'] += np.random.normal(0, 5)
        
        # Clip values
        base_case['urgency_score'] = np.clip(base_case['urgency_score'], 0, 1)
        base_case['medical_risk_score'] = np.clip(base_case['medical_risk_score'], 0, 1)
        base_case['children_present_score'] = np.clip(base_case['children_present_score'], 0, 1)
        base_case['sentiment_score'] = np.clip(base_case['sentiment_score'], -1, 1)
        base_case['actual_priority'] = np.clip(base_case['actual_priority'], 0, 100)
        
        training_cases.append(base_case)
    
    return training_cases

def main():
    print("Starting AI model training...")
    
    # Initialize AI service
    ai_service = AIService()
    
    # Generate training data
    print("Generating training data...")
    training_data = generate_training_data()
    
    # Train priority model
    print("Training priority scoring model...")
    ai_service.train_priority_model(training_data)
    
    print("✅ AI models trained successfully!")
    print(f"Trained on {len(training_data)} cases")
    
    # Test the model
    print("\nTesting model on sample cases...")
    test_cases = [
        "URGENT! My child needs immediate surgery. Life-threatening condition!",
        "Looking for help with school fees for next semester",
        "Need food assistance for my family of 5",
        "Elderly parent needs medical equipment, very critical situation"
    ]
    
    for test in test_cases:
        result = ai_service.analyze_case_comprehensive({'description': test})
        print(f"\nText: {test[:50]}...")
        print(f"Priority Score: {result['priority_score']:.1f}")
        print(f"Urgency: {result['urgency']['level']} ({result['urgency']['score']:.2f})")
        print(f"Medical Risk: {result['medical_risk']['level']}")
        print(f"Children Present: {result['children']['present']}")
        print(f"Category: {result['category']['category']}")

if __name__ == "__main__":
    main()