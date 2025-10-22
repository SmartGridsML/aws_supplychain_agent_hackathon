# Supply Chain AI Agent

Enterprise-grade AI agent for supply chain management powered by AWS Bedrock and Claude 3.7 Sonnet.

## 🌐 **LIVE DEMO**
**🚀 Try it now: http://supply-chain-ai-1761172496.s3-website-us-east-1.amazonaws.com**

## 🏗️ Architecture

**✅ AWS Requirements Met:**
- **LLM**: Claude 3.7 Sonnet on AWS Bedrock
- **Agent Core**: Bedrock Agent with 5 action groups
- **Autonomous**: Multi-step reasoning and decision making
- **Integrations**: 8 Lambda functions, multiple APIs, real-time data

## 🚀 Quick Deploy

### Option 1: CloudFormation (Recommended)
```bash
aws cloudformation create-stack \
  --stack-name supply-chain-ai \
  --template-body file://cloudformation-template.yaml \
  --region us-east-1
```

### Option 2: Simple S3 Deploy
```bash
chmod +x deploy.sh
./deploy.sh
```

## 🎯 System Components

### Bedrock Agent (CXLLJNZOCS)
- **Model**: Claude 3.7 Sonnet (`anthropic.claude-3-7-sonnet-20250219-v1:0`)
- **Action Groups**: 5 (Risk Analysis, Tracking, Orchestrator, User Input, Search)
- **Status**: PREPARED and ready

### Lambda Functions (8 total)
- `TrackingExecutor`: Flight/vessel tracking with API fallbacks
- `SearchExecutor`: SerpAPI + NewsAPI integration
- `AutonomousOrchestrator`: Multi-step reasoning
- `RiskAnalyzer`: Supply chain risk assessment
- `GeopoliticalScanner`: Real-time event monitoring

### Frontend
- React + TypeScript with sleek dark UI
- Real-time chat interface
- Metadata visualization
- Responsive design

## 🌐 Live System URLs

- **Website**: http://supply-chain-ai-1761172496.s3-website-us-east-1.amazonaws.com
- **API**: `https://qib5nbuglb.execute-api.us-east-1.amazonaws.com/prod`
- **Agent ID**: `CXLLJNZOCS`

## 🔧 Local Development

```bash
cd frontend
npm install
npm run dev
```

## 📊 Capabilities

- **Vessel Tracking**: Real AIS data (MMSI, IMO, vessel names)
- **Flight Monitoring**: Live aircraft positions and status
- **Risk Analysis**: Multi-factor supply chain assessments
- **Geopolitical Intelligence**: Real-time disruption monitoring
- **Autonomous Orchestration**: Multi-step decision making
- **Search Integration**: Web search and news analysis

## 💰 Cost Optimization

- **Free Tier Services**: S3, Lambda, API Gateway
- **Pay-per-use**: Bedrock Claude 3.7 Sonnet (~$0.73/month for testing)
- **Total Monthly Cost**: <$1 for hackathon usage

## 🏆 Competition Compliance

This agent meets all AWS AI Agent requirements:
- ✅ Bedrock LLM (Claude 3.7 Sonnet)
- ✅ Bedrock Agent Core with primitives
- ✅ Reasoning capabilities for decision-making
- ✅ Autonomous task execution
- ✅ External API integrations
- ✅ Multi-service AWS architecture
