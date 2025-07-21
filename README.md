# Agent AI Foundry – Azure Function Wrapper

Azure Function wrapper serving Agent AI Foundry agents.

### 🔧 Prerequisites

You need to create your agent using the Agent AI Foundry Agent Service. To create an agent via SDK or integrate it with a tool, check the tool use patterns in [agent-ai-foundry-tool-use](https://github.com/kimtth/agent-ai-foundry-tool-use)

### 🔧 Background

The link only supports single-turn conversations and does not handle threaded interactions. The functions provide two endpoints: one for `creating a chat` and another for `continuing a conversation with an agent using a thread ID`.

> 💡 [Integrate Custom Azure AI Agents with CoPilot Studio and M365 CoPilot](https://techcommunity.microsoft.com/blog/aiplatformblog/integrate-custom-azure-ai-agents-with-copilot-studio-and-m365-copilot/4405070)

###  Deployment

Use the Azure Functions Core Tools to publish your Python function app:

```bash
func azure functionapp publish <your-func-app-name> --python
```
