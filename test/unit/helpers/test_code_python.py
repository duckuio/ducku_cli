"""Tests for Python code entity extraction."""

from pathlib import Path
from src.core.code.dispatcher import collect_code_entities_from_content


def test_collect_all_python_entities():
    """Test collecting all entity types from a comprehensive Python file."""
    code = '''
# Module-level dictionary with string keys and values
SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript"
}

# Module-level list with string elements
ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE"]

# Mixed dictionary (won't extract values because not all are strings)
CONFIG = {
    "host": "localhost",
    "port": 8080,
    "timeout": 30
}

# Module-level function
def calculate_total(items, tax_rate):
    return sum(items) * (1 + tax_rate)

def process_data(data: str, options: dict = None) -> bool:
    return True

class UserService:
    """Service class for user operations."""
    
    # Class-level dictionary with string keys only
    ROLES = {
        "admin": 1,
        "user": 2,
        "guest": 3
    }
    
    # Class-level dictionary with string values only
    STATUS_MESSAGES = {
        "active": "User is active",
        "inactive": "User is inactive",
        "banned": "User is banned"
    }
    
    # Class-level list
    PERMISSIONS = ["read", "write", "execute"]
    
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
        self.email = None
    
    def update_profile(self, email, phone):
        self.email = email
        self.phone = phone
    
    @classmethod
    def from_dict(cls, data):
        return cls(data["name"], data["age"])

class OrderProcessor:
    def __init__(self):
        self.items = []
        self.config = {
            "retries": 3,
            "delay": 1000
        }
        # Dict in method with string values
        self.messages = {
            "success": "Order processed",
            "error": "Failed to process"
        }
        # List in method
        self.statuses = ["pending", "confirmed", "shipped"]
    
    def process(self, order_id: int) -> dict:
        return {"status": "processed"}
'''
    
    # Create temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = Path(f.name)
    
    try:
        entities = []
        collect_code_entities_from_content(temp_path, entities)
        
        # Check module-level functions
        module_funcs = [c for c in entities if c.type == "module_functions"]
        assert len(module_funcs) == 1
        func_names = {e.name for e in module_funcs[0].entities}
        assert func_names == {"calculate_total", "process_data"}
        
        # Check module-level classes
        module_classes = [c for c in entities if c.type == "module_classes"]
        assert len(module_classes) == 1
        class_names = {e.name for e in module_classes[0].entities}
        assert class_names == {"UserService", "OrderProcessor"}
        
        # Check module-level dict keys
        supported_ext_keys = [c for c in entities if c.type == "dict_keys" and "SUPPORTED_EXTENSIONS" in c.parent]
        assert len(supported_ext_keys) == 1
        assert {e.name for e in supported_ext_keys[0].entities} == {".py", ".js", ".ts"}
        
        # Check module-level dict values
        supported_ext_values = [c for c in entities if c.type == "dict_values" and "SUPPORTED_EXTENSIONS" in c.parent]
        assert len(supported_ext_values) == 1
        assert {e.name for e in supported_ext_values[0].entities} == {"python", "javascript", "typescript"}
        
        # Check module-level list elements
        allowed_methods_list = [c for c in entities if c.type == "list_elements" and "ALLOWED_METHODS" in c.parent]
        assert len(allowed_methods_list) == 1
        assert {e.name for e in allowed_methods_list[0].entities} == {"GET", "POST", "PUT", "DELETE"}
        
        # Check CONFIG dict keys (mixed values - should have keys but not values)
        config_keys = [c for c in entities if c.type == "dict_keys" and c.parent.endswith("::CONFIG")]
        assert len(config_keys) == 1
        assert {e.name for e in config_keys[0].entities} == {"host", "port", "timeout"}
        
        config_values = [c for c in entities if c.type == "dict_values" and c.parent.endswith("::CONFIG")]
        assert len(config_values) == 0  # Mixed types, should not extract values
        
        # Check function arguments
        calc_args = [c for c in entities if c.type == "function_arguments" and "calculate_total" in c.parent]
        assert len(calc_args) == 1
        assert {e.name for e in calc_args[0].entities} == {"items", "tax_rate"}
        
        process_args = [c for c in entities if c.type == "function_arguments" and "process_data" in c.parent]
        assert len(process_args) == 1
        assert {e.name for e in process_args[0].entities} == {"data", "options"}
        
        # Check UserService class methods
        user_methods = [c for c in entities if c.type == "class_methods" and "UserService" in c.parent]
        assert len(user_methods) == 1
        method_names = {e.name for e in user_methods[0].entities}
        assert method_names == {"__init__", "update_profile", "from_dict"}
        
        # Check UserService properties
        user_props = [c for c in entities if c.type == "class_properties" and "UserService" in c.parent]
        assert len(user_props) == 1
        prop_names = {e.name for e in user_props[0].entities}
        assert prop_names == {"name", "age", "email", "phone"}
        
        # Check UserService ROLES dict keys
        roles_keys = [c for c in entities if c.type == "dict_keys" and "ROLES" in c.parent]
        assert len(roles_keys) == 1
        assert {e.name for e in roles_keys[0].entities} == {"admin", "user", "guest"}
        
        # Check UserService STATUS_MESSAGES dict keys and values
        status_keys = [c for c in entities if c.type == "dict_keys" and "STATUS_MESSAGES" in c.parent]
        assert len(status_keys) == 1
        assert {e.name for e in status_keys[0].entities} == {"active", "inactive", "banned"}
        
        status_values = [c for c in entities if c.type == "dict_values" and "STATUS_MESSAGES" in c.parent]
        assert len(status_values) == 1
        assert {e.name for e in status_values[0].entities} == {"User is active", "User is inactive", "User is banned"}
        
        # Check UserService PERMISSIONS list
        permissions_list = [c for c in entities if c.type == "list_elements" and "PERMISSIONS" in c.parent]
        assert len(permissions_list) == 1
        assert {e.name for e in permissions_list[0].entities} == {"read", "write", "execute"}
        
        # Check __init__ method arguments (should exclude self)
        init_args = [c for c in entities if c.type == "function_arguments" and "UserService::__init__" in c.parent]
        assert len(init_args) == 1
        assert {e.name for e in init_args[0].entities} == {"name", "age"}
        assert "self" not in {e.name for e in init_args[0].entities}
        
        # Check from_dict classmethod arguments (should exclude cls)
        from_dict_args = [c for c in entities if c.type == "function_arguments" and "from_dict" in c.parent]
        assert len(from_dict_args) == 1
        assert {e.name for e in from_dict_args[0].entities} == {"data"}
        assert "cls" not in {e.name for e in from_dict_args[0].entities}
        
        # Check OrderProcessor
        order_methods = [c for c in entities if c.type == "class_methods" and "OrderProcessor" in c.parent]
        assert len(order_methods) == 1
        assert {e.name for e in order_methods[0].entities} == {"__init__", "process"}
        
        # Check OrderProcessor properties
        order_props = [c for c in entities if c.type == "class_properties" and "OrderProcessor" in c.parent]
        assert len(order_props) == 1
        assert {e.name for e in order_props[0].entities} == {"items", "config", "messages", "statuses"}
        
        # Check OrderProcessor config dict (inside __init__, mixed types)
        config_dict_keys = [c for c in entities if c.type == "dict_keys" and "OrderProcessor::__init__::config" in c.parent]
        assert len(config_dict_keys) == 1
        assert {e.name for e in config_dict_keys[0].entities} == {"retries", "delay"}
        
        # Check OrderProcessor messages dict (inside __init__, string values)
        messages_keys = [c for c in entities if c.type == "dict_keys" and "OrderProcessor::__init__::messages" in c.parent]
        assert len(messages_keys) == 1
        assert {e.name for e in messages_keys[0].entities} == {"success", "error"}
        
        messages_values = [c for c in entities if c.type == "dict_values" and "OrderProcessor::__init__::messages" in c.parent]
        assert len(messages_values) == 1
        assert {e.name for e in messages_values[0].entities} == {"Order processed", "Failed to process"}
        
        # Check OrderProcessor statuses list (inside __init__)
        statuses_list = [c for c in entities if c.type == "list_elements" and "OrderProcessor::__init__::statuses" in c.parent]
        assert len(statuses_list) == 1
        assert {e.name for e in statuses_list[0].entities} == {"pending", "confirmed", "shipped"}
        
    finally:
        temp_path.unlink()
