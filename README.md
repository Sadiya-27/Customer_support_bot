# Customer_support_bot

# 🧠 AI Chatbot for IT Support on AWS

## 📋 Overview
The AI Chatbot for IT Support is a serverless, NLP-powered chatbot built using Amazon Lex, AWS Lambda, DynamoDB, and Amazon SES.
It serves as the first line of technical support, handling routine IT queries such as:
  1. Password resets
  2. Wi-Fi connectivity issues
  3. Email login/access problems
When the chatbot cannot resolve a query, it automatically escalates it to a human IT agent via Amazon SES.
The frontend is hosted as a static web page on Amazon S3 for easy user interaction.

## Demo Link: https://itservicebot.s3.us-east-1.amazonaws.com/bot.html 

--- 

## 🏗️ Architecture
<img width="1536" height="1024" alt="ChatGPT Image Nov 12, 2025, 03_11_36 PM" src="https://github.com/user-attachments/assets/ca0a10b6-897b-42fb-a6a9-baf8a5754258" />


Flow:
1. User sends a message on the web interface.
2. Amazon Lex recognizes the intent (e.g., WiFiIssue, PasswordReset).
3. Lambda checks DynamoDB for a stored response.
4. If found → sends answer back to user.
5. If not found → sends the query to IT support via SES email.
6. All interactions are logged in DynamoDB.

--- 

## ⚙️ Technologies Used
| Component          | Service / Tool        | Purpose                                                  |
| ------------------ | --------------------- | -------------------------------------------------------- |
| **Chatbot Engine** | Amazon Lex            | Natural language understanding (intents, utterances)     |
| **Backend Logic**  | AWS Lambda            | Executes chatbot logic, fetches FAQ, triggers SES        |
| **Database**       | Amazon DynamoDB       | Stores FAQs and query logs                               |
| **Email Service**  | Amazon SES            | Sends unresolved queries to IT support staff             |
| **Hosting**        | Amazon S3             | Hosts static chatbot frontend                            |
| **Security**       | IAM, VPC              | Manages access control and internal network restrictions |
| **Frontend**       | HTML, CSS, JavaScript | Chat interface for users                                 |

--- 

## 💬 Supported Intents
| Intent                  | Example Utterances                                 | Action                                         |
| ----------------------- | -------------------------------------------------- | ---------------------------------------------- |
| **PasswordResetIntent** | “I forgot my password”, “Reset my password”        | Provides reset instructions                    |
| **WiFiIssueIntent**     | “My Wi-Fi isn’t working”, “No internet connection” | Suggests troubleshooting steps                 |
| **EmailAccessIntent**   | “I can’t access my email”, “Email not opening”     | Guides user to check credentials or contact IT |
| **FallbackIntent**      | Unknown query                                      | Escalates to IT support via SES                |

---

## 🧾 DynamoDB Sample Data

Your DynamoDB table (ITSupportFAQs) might look like this:

| faq_id          | intent         | question                    | answer                                                                               | keywords                |
| --------------- | -------------- | --------------------------- | ------------------------------------------------------------------------------------ | ----------------------- |
| faq_001         | password_reset | How do I reset my password? | Visit [https://example.com/reset](https://example.com/reset) to reset your password. | password, reset, forgot |
| faq_wifi_home   | wifi_issue     | My Wi-Fi is not working     | Restart your router or contact your ISP.                                             | wifi, home, network     |
| faq_wifi_office | wifi_issue     | Office Wi-Fi not connecting | Check your SSID or contact IT.                                                       | wifi, office, internet  |
| faq_003         | emailaccess    | Having trouble with email.  | Check internet and credentials.                                                      | email, login, opening   |

---

## ⚙️ Setup Instructions

### 1. Frontend (S3 Hosting)
- Upload files from /frontend/:
- index.html, style.css, script.js
- Enable Static Website Hosting in S3.
- Configure your AWS SDK credentials in aws-config.js:
``` bash
AWS.config.region = "us-east-1";
AWS.config.credentials = new AWS.CognitoIdentityCredentials({
  IdentityPoolId: "YOUR_COGNITO_IDENTITY_POOL_ID"
});
```

### 2. Amazon Lex
- Create a new Lex bot named ITSupportBot.
- Add intents:
  - PasswordResetIntent
  - WiFiIssueIntent
  - EmailAccessIntent
  - FallbackIntent
- Add sample utterances for each intent.
- Link fulfillment to your AWS Lambda function.

### 3. AWS Lambda
- Create a Lambda function (Python/Node.js) using /lambda/handler.py.
- Add permissions for:
  - dynamodb:GetItem, dynamodb:PutItem
  - ses:SendEmail
- Set Lex as an event source for fulfillment.

### 4. DynamoDB
- Create table: ITSupportFAQs
  - Primary key: faq_id (String)
- Import data from sample_data.json (via AWS Console or CLI).

### 5. Amazon SES
- Verify your sender and receiver email addresses.
- Allow the Lambda function to send emails through SES.

--- 

## 🔒 Security Configuration
- Use IAM roles to grant least-privilege access.
- Optionally, configure VPC access for internal deployments.
- Encrypt data in DynamoDB at rest.

---

## 🧩 Features
- Handles common IT queries (Wi-Fi, password, email)
- Automatically escalates unresolved issues to human agents
- Learns and improves using logged queries
- Scalable and cost-effective (serverless)
- Secure AWS-based integration

---

## 📈 Future Enhancements
1. Add Amazon Kendra for advanced FAQ retrieval
2. Use Amazon Polly for text-to-speech
3. Integrate AWS QuickSight for analytics
4. Add ServiceNow / Jira integration for ticket tracking
5. Enable multi-language support with Amazon Translate

--- 

## 🧪 Testing Scenarios
| Test Case      | Input                        | Expected Output                    |
| -------------- | ---------------------------- | ---------------------------------- |
| Password Reset | “I forgot my password”       | Bot provides reset instructions    |
| Wi-Fi Issue    | “My Wi-Fi isn’t connecting”  | Bot suggests troubleshooting steps |
| Unknown Query  | “How do I get admin access?” | Escalated to IT support via SES    |
| Low Confidence | Random sentence              | Stored for retraining              |

