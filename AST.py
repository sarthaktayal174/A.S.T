import ast
from pymongo import MongoClient

def parse_condition(condition):
    """Parse a condition like 'age > 30' or 'department == "Sales"'."""
    # Split condition to extract field, operator, and value
    field, operator, value = condition.split()
    
    # Convert value to the appropriate type (int or str)
    try:
        value = int(value)
    except ValueError:
        value = value.strip('"').strip("'")
    
    return field, operator, value

class TreeNode:
    def __init__(self, node_type, value=None, left=None, right=None):
        self.node_type = node_type  # 'operator' or 'operand'
        self.value = value  # Operand condition or operator like AND/OR
        self.left = left  # Left child (TreeNode)
        self.right = right  # Right child (TreeNode)

    def __repr__(self):
        return f"TreeNode(type={self.node_type}, value={self.value})"
    
def node_to_dict(node):
    """Convert TreeNode to a dictionary suitable for MongoDB."""
    if node is None:
        return None
    node_dict = {
        "node_type": node.node_type,
        "value": node.value,
        "left": node_to_dict(node.left),
        "right": node_to_dict(node.right)
    }
    return node_dict

def create_rule(rule_string):
    """Parse the rule string into an AST (Tree of TreeNodes)."""
    rule_string = rule_string.strip()
    rule_string = rule_string.lower()
    rule_tree = ast.parse(rule_string, mode='eval').body
    
    def build_ast(node):
        """Recursively build the AST from the Python AST nodes."""
        if isinstance(node, ast.BoolOp):
            # AND/OR operation (BoolOp)
            if isinstance(node.op, ast.And):
                node_type = 'operator'
                value = 'AND'
            elif isinstance(node.op, ast.Or):
                node_type = 'operator'
                value = 'OR'
            return TreeNode(node_type, value, build_ast(node.values[0]), build_ast(node.values[1]))
        
        elif isinstance(node, ast.Compare):
            # Comparisons like 'age > 30'
            left = node.left.id  # Left side of the comparison, e.g., 'age'
            comparator = node.ops[0]  # Comparison operator, e.g., '>'
            right = node.comparators[0]  # Value being compared, e.g., '30'
            
            # Convert the comparator (operator) to a string
            if isinstance(comparator, ast.Gt):
                operator = '>'
            elif isinstance(comparator, ast.Lt):
                operator = '<'
            elif isinstance(comparator, ast.Eq):
                operator = '=='
            
            # Handle the right side (the value being compared to)
            if isinstance(right, ast.Constant):
                value = right.value
            elif isinstance(right, ast.Str):
                value = right.s  # For Python <3.8 compatibility
            
            condition = f"{left} {operator} {value}"
            return TreeNode("operand", condition)

    return build_ast(rule_tree)

def combine_rules(rule_strings):
    """Combine multiple rules into a single AST."""
    # Convert each rule string into an AST
    asts = [create_rule(rule) for rule in rule_strings]
    
    # Combine all ASTs under a single AND node for simplicity
    if len(asts) > 1:
        combined_root = TreeNode("operator", "AND", asts[0], asts[1])
        for ast in asts[2:]:
            combined_root = TreeNode("operator", "AND", combined_root, ast)
        return combined_root
    else:
        return asts[0]
    
def dict_to_node(node_dict):
    """Convert a dictionary back to a TreeNode."""
    if node_dict is None:
        return None
    node = TreeNode(
        node_type=node_dict["node_type"],
        value=node_dict["value"],
        left=dict_to_node(node_dict["left"]),
        right=dict_to_node(node_dict["right"])
    )
    return node


def evaluate_operand(condition, data):
    """Evaluate a condition like 'age > 30' against the data."""
    field, operator, value = parse_condition(condition)
    field_value = data.get(field)
    
    if operator == '>':
        return field_value > value
    elif operator == '<':
        return field_value < value
    elif operator == '==':
        return field_value == value
    elif operator == '!=':
        return field_value != value



def evaluate_rule(node, data):
    """Recursively evaluate the AST against the data."""
    if node.node_type == 'operand':
        # If it's an operand, evaluate the condition
        return evaluate_operand(node.value, data)
    
    elif node.node_type == 'operator':
        # If it's an operator (AND/OR), evaluate both left and right children
        left_result = evaluate_rule(node.left, data)
        right_result = evaluate_rule(node.right, data)
        
        if node.value == 'AND':
            return left_result and right_result
        elif node.value == 'OR':
            return left_result or right_result

# Initialize MongoDB client and define the database and collection
client = MongoClient("mongodb://localhost:27017/")
db = client["rule_database"]
ast_collection = db["ast_collection"]

# Test the rule
rule_str1 = "(age > 35 AND salary > 50000) OR (((age > 30 AND department == 'Sales') OR (age < 25 AND department == 'Marketing')) AND (salary > 50000 OR experience > 5))"
rule_str2 = "((age > 30 AND department == 'Marketing')) AND (salary > 20000 OR experience > 5)"



# Create and store the AST for rule 1
# ast_root1 = create_rule(rule_str1)
# ast_document1 = node_to_dict(ast_root1)
# ast_document1["_id"] = "rule1"  # Set an identifier for the rule
# ast_collection.insert_one(ast_document1)

# # Create and store the AST for rule 2
# ast_root2 = create_rule(rule_str2)
# ast_document2 = node_to_dict(ast_root2)
# ast_document2["_id"] = "rule2"  # Set an identifier for the rule
# ast_collection.insert_one(ast_document2)

# rule_id = "rule1"  # replace with your rule's identifier
# ast_document = ast_collection.find_one({"_id": rule_id})


task=input("would you like to 'create' a rule or 'check' the validity of one?(type 'create' OR 'check')")

if task.lower() =="create":
    rule_id=input("Enter a name for this rule(eg. rule_1):")
    while(ast_collection.find_one({"_id": rule_id})):
        rule_id=input("A rule from this id already exists enter a different rule id:")
    rule_str= input("Enter the rule:")
    ast_root= create_rule(rule_str)
    ast_document = node_to_dict(ast_root)
    ast_document["_id"] = rule_id
    ast_collection.insert_one(ast_document)
elif task.lower() =="check":
    rule_id=input("enter the rule_id of the  for which you want to evaluate:")
    ast_document = ast_collection.find_one({"_id": rule_id})
    while not ast_document:
        rule_id=input("The rule_id you enterd does not exis in the data base, please enter a valid rule_id:")
    rule_ast = dict_to_node(ast_document)
    age=int(input("Enter age:"))
    salary=int(input("Enter salary:"))
    department=input("Enter department:").lower()
    experience=int(input("Enter experience:"))
    data={
        "age": age,
        "salary": salary,
        "department": department,
        "experience": experience
    }
    if evaluate_rule(rule_ast,data=data):
        print (f"The data you entered is valid for {rule_id}")
    else:
        print (f"The data you entered is valid for {rule_id}")



