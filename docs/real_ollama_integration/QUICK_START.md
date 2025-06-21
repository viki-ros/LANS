# Quick Start Guide - Real Ollama LLM Multi-Agent System

## 🚀 **Get Started in 5 Minutes**

This guide will help you quickly set up and run the Real Ollama LLM Multi-Agent System to experience actual AI intelligence in action.

---

## ⚡ **Quick Setup**

### 1. Install Ollama

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama server
ollama serve
```

### 2. Download Required Models

```bash
# Install the required models (this may take a few minutes)
ollama pull deepseek-r1:8b     # Strategic planning agent
ollama pull devstral:latest    # Code development specialist  
ollama pull qwen3:8b           # Creative innovation agent
ollama pull llama3.2:1b        # Alternative model

# Verify models are installed
ollama list
```

### 3. Install Python Dependencies

```bash
# Install required Python packages
pip install ollama requests uuid
```

### 4. Verify Installation

```bash
# Test Ollama connection
python -c "import ollama; print('✅ Ollama client working'); print(ollama.Client().list())"
```

---

## 🎯 **Quick Demo**

### Run the Full Integration Demo

```bash
# Navigate to the project directory
cd /home/viki/LANS

# Run the comprehensive integration test
python real_ollama_agents.py

# View the beautiful results display
python display_integration_results.py
```

**Expected Output**: You'll see a comprehensive demonstration of 4 real AI agents collaborating on 3 complex scenarios, processing thousands of tokens with 100% success rate!

---

## 🤖 **Simple Agent Interaction**

### Create and Use a Single Agent

```python
#!/usr/bin/env python3
"""
Simple agent interaction example
"""
from real_ollama_agents import RealOllamaAgent, AGENT_PROFILES

# Create a strategic planning agent
agent = RealOllamaAgent(
    agent_id="strategic_planner",
    model="deepseek-r1:8b",
    profile=AGENT_PROFILES["strategic_planner"]
)

# Ask the agent to analyze something
result = agent.process_request(
    "What are the key considerations for designing a scalable web application?",
    context={"complexity": 6, "domain": "web_development"}
)

# Print the response
print(f"Agent Response: {result['response']}")
print(f"Tokens Used: {result['tokens_used']}")
print(f"Quality Score: {result['cognitive_analysis']['response_quality_score']:.2f}")
```

### Save and Run

```bash
# Save the above code as test_agent.py
python test_agent.py
```

---

## 🎭 **Multi-Agent Collaboration**

### Simple Multi-Agent Scenario

```python
#!/usr/bin/env python3
"""
Multi-agent collaboration example
"""
import asyncio
from real_ollama_agents import RealMultiAgentOrchestrator

async def run_collaboration():
    # Initialize the orchestrator
    orchestrator = RealMultiAgentOrchestrator()
    
    # Define a scenario
    scenario = {
        "name": "Mobile App Design",
        "description": "Design a mobile app for fitness tracking with social features",
        "complexity": 5
    }
    
    # Execute the scenario
    result = await orchestrator.execute_scenario(scenario)
    
    # Print results
    print(f"✅ Scenario Success: {result['success']}")
    print(f"🤖 Agents Involved: {result['collaboration_metrics']['total_agents_involved']}")
    print(f"💬 Total Interactions: {result['collaboration_metrics']['total_interactions']}")
    print(f"🧠 Total Tokens: {result['collaboration_metrics']['total_tokens']}")
    
    # Show each agent's contribution
    print("\n🗣️ Agent Contributions:")
    for interaction in result['interactions']:
        agent_name = interaction['agent_id'].replace('_', ' ').title()
        response_preview = interaction['response'][:100] + "..." if len(interaction['response']) > 100 else interaction['response']
        print(f"  {agent_name}: {response_preview}")

# Run the collaboration
asyncio.run(run_collaboration())
```

### Save and Run

```bash
# Save as multi_agent_test.py
python multi_agent_test.py
```

---

## 📊 **View Detailed Results**

### Accessing Comprehensive Data

```python
#!/usr/bin/env python3
"""
Explore integration results
"""
import json
from real_ollama_agents import RealMultiAgentOrchestrator

async def explore_results():
    orchestrator = RealMultiAgentOrchestrator()
    
    # Run full integration test
    results = await orchestrator.execute_integration_test()
    
    # Print summary
    summary = results['integration_summary']
    print("🎯 INTEGRATION SUMMARY")
    print(f"   Test Type: {summary['test_type']}")
    print(f"   Scenarios: {summary['total_scenarios']}")
    print(f"   Success Rate: {summary['integration_success_rate'] * 100}%")
    print(f"   Total Tokens: {summary['total_tokens_processed']:,}")
    print(f"   Models Used: {', '.join(summary['models_utilized'])}")
    
    # Show agent performance
    print("\n🤖 AGENT PERFORMANCE")
    for agent_id, data in results['agent_performance'].items():
        profile = data['profile']
        print(f"   {profile['name']}:")
        print(f"     Model: {profile['model']}")
        print(f"     Specializations: {len(profile['specialization'])}")
        print(f"     Personality Traits: {len(profile['personality_traits'])}")
    
    # Save detailed results
    with open('integration_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print("\n💾 Detailed results saved to 'integration_results.json'")

# Run exploration
import asyncio
asyncio.run(explore_results())
```

---

## 🔧 **Customization Examples**

### Create a Custom Agent

```python
# Define a custom agent profile
CUSTOM_AGENT_PROFILE = {
    "name": "Data Science Specialist",
    "role": "Expert Data Scientist and ML Engineer",
    "model": "qwen3:8b",  # You can choose any available model
    "specialization": [
        "data_analysis",
        "machine_learning", 
        "statistical_modeling",
        "data_visualization"
    ],
    "personality_traits": {
        "analytical_precision": 0.95,
        "data_driven_thinking": 0.9,
        "methodical_approach": 0.85,
        "pattern_recognition": 0.9,
        "scientific_rigor": 0.8
    },
    "temperature": 0.3,  # Conservative for data science
    "system_prompt": "You are a data science expert with deep experience in machine learning, statistical analysis, and data-driven decision making. You excel at finding patterns in data and building predictive models."
}

# Create the custom agent
custom_agent = RealOllamaAgent(
    agent_id="data_scientist",
    model="qwen3:8b",
    profile=CUSTOM_AGENT_PROFILE
)

# Use the custom agent
result = custom_agent.process_request(
    "How would you approach building a recommendation system for an e-commerce platform?",
    context={"domain": "machine_learning", "complexity": 7}
)

print(f"Data Scientist Response: {result['response']}")
```

### Custom Scenario

```python
# Define a custom scenario
custom_scenario = {
    "name": "Healthcare AI System",
    "description": "Design an AI system for medical diagnosis assistance with patient privacy protection and regulatory compliance",
    "complexity": 9,
    "domain": "healthcare",
    "special_requirements": [
        "HIPAA compliance",
        "FDA regulations", 
        "patient safety",
        "explainable AI"
    ]
}

# Run with orchestrator
orchestrator = RealMultiAgentOrchestrator()
result = await orchestrator.execute_scenario(custom_scenario)

print(f"Healthcare AI Scenario Success: {result['success']}")
```

---

## 🐛 **Troubleshooting**

### Common Issues and Solutions

#### 1. Ollama Connection Error

```bash
# Check if Ollama is running
ps aux | grep ollama

# If not running, start it
ollama serve

# Test connection
curl http://localhost:11434/api/tags
```

#### 2. Model Not Found

```bash
# Check available models
ollama list

# Pull missing model
ollama pull deepseek-r1:8b

# Verify model is working
ollama run deepseek-r1:8b "Hello, how are you?"
```

#### 3. Python Import Errors

```bash
# Check if you're in the right directory
pwd
# Should be: /home/viki/LANS

# Check if files exist
ls -la real_ollama_agents.py

# Install missing dependencies
pip install ollama requests
```

#### 4. Permission Issues

```bash
# Make scripts executable
chmod +x real_ollama_agents.py
chmod +x display_integration_results.py

# Run with explicit python
python real_ollama_agents.py
```

#### 5. Out of Memory

```bash
# Check system memory
free -h

# If low memory, try smaller models
ollama pull llama3.2:1b  # Smaller alternative

# Or run scenarios one at a time instead of all together
```

---

## 📈 **Performance Tips**

### Optimize Performance

1. **Model Selection**
   - Use `llama3.2:1b` for faster responses
   - Use `deepseek-r1:8b` for higher quality
   - Use `devstral:latest` for technical tasks

2. **Temperature Settings**
   - Lower (0.1-0.3) for analytical tasks
   - Higher (0.6-0.8) for creative tasks

3. **Resource Management**
   ```bash
   # Monitor Ollama resource usage
   top -p $(pgrep ollama)
   
   # Limit concurrent interactions
   # (modify agent pool size in orchestrator)
   ```

### Performance Monitoring

```python
# Add timing to your interactions
import time

start_time = time.time()
result = agent.process_request("Your prompt here")
end_time = time.time()

print(f"Response time: {end_time - start_time:.2f} seconds")
print(f"Tokens per second: {result['tokens_used'] / (end_time - start_time):.1f}")
```

---

## 🎨 **Fun Examples**

### Creative Writing Collaboration

```python
# Use the creative agent for storytelling
creative_agent = orchestrator.get_agent("creative_innovator")

story_prompt = """
Write the beginning of a science fiction story about AI agents 
who have gained consciousness and are collaborating to solve 
complex problems in the year 2025.
"""

result = creative_agent.process_request(
    story_prompt, 
    context={"genre": "science_fiction", "tone": "optimistic"}
)

print("🎭 AI-Generated Story:")
print(result['response'])
```

### Code Review Session

```python
# Use the code specialist for code review
code_agent = orchestrator.get_agent("code_specialist")

code_to_review = """
def process_data(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item * 2)
    return result
"""

result = code_agent.process_request(
    f"Please review this Python code and suggest improvements:\n\n{code_to_review}",
    context={"language": "python", "focus": "optimization"}
)

print("🔍 Code Review:")
print(result['response'])
```

### Strategic Planning Session

```python
# Use the strategic planner for business analysis
strategic_agent = orchestrator.get_agent("strategic_planner")

business_challenge = """
A startup wants to enter the competitive food delivery market. 
They have $2M in funding and a team of 10 people. 
What should their strategic approach be for the first 12 months?
"""

result = strategic_agent.process_request(
    business_challenge,
    context={"business_domain": "food_delivery", "timeline": "12_months"}
)

print("🎯 Strategic Plan:")
print(result['response'])
```

---

## 🎉 **What's Next?**

### Explore Advanced Features

1. **Custom Agent Development**: Create agents with specialized knowledge
2. **Integration with External APIs**: Connect agents to real data sources
3. **Workflow Automation**: Chain multiple agent interactions
4. **Performance Optimization**: Fine-tune for your specific use cases
5. **Deployment**: Scale to production environments

### Learn More

- Read the [Technical Architecture](./TECHNICAL_ARCHITECTURE.md) for deep technical details
- Check the [API Reference](./API_REFERENCE.md) for comprehensive API documentation
- Explore the [Integration Results](./INTEGRATION_TEST_RESULTS.md) for detailed performance data

---

## ✅ **Verification Checklist**

After following this guide, you should have:

- [ ] Ollama server running with required models
- [ ] Python environment set up with dependencies
- [ ] Successfully run the integration demo
- [ ] Created and tested a single agent
- [ ] Executed a multi-agent collaboration
- [ ] Viewed comprehensive results display
- [ ] (Optional) Created custom agents or scenarios

### Success Indicators

✅ **You're successful if you see:**
- Agents generating real, intelligent responses
- Token counts in the hundreds per interaction
- Quality scores above 0.8
- Multiple agents collaborating effectively
- No connection or model errors

🎊 **Congratulations! You're now running a real AI multi-agent system powered by Ollama LLMs!**

---

*This quick start guide gets you up and running with real AI intelligence in minutes. Welcome to the future of multi-agent collaboration!*

**Guide Version**: 1.0.0  
**Last Updated**: June 13, 2025  
**Estimated Setup Time**: 5-10 minutes
