# Rule Engine with Abstract Syntax Tree (AST)

This project implements a simple rule engine using an Abstract Syntax Tree (AST) to determine user eligibility based on various attributes like age, department, salary, and experience. The engine allows creating dynamic rules and storing them in MongoDB for evaluation against user data.

## Features

- **Create Dynamic Rules**: Supports rule creation with logical operators (`AND`, `OR`) and conditional operators (`>`, `<`, `==`, `!=`).
- **Store Rules in MongoDB**: Rules are stored in MongoDB as nested documents representing the AST structure.
- **Evaluate Rules**: Evaluates input data against stored rules and determines whether the data satisfies the rule conditions.

## Technology Stack

- **Python**: Core programming language for the rule engine logic.
- **MongoDB**: NoSQL database to store ASTs of the rules.
- **pymongo**: Python MongoDB driver for database interactions.

## Getting Started

### Prerequisites

1. Python 3.x
2. MongoDB (ensure MongoDB server is running locally on port `27017`)
3. Required Python packages (install with `pip`):

   ```bash
   pip install pymongo
