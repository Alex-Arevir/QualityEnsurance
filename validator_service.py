class Validator:

    def valid_less_to_length_str(data: str, length: int):
        if len(data) < length:
            return False
        return True
    
    def valid_numeric_type(*args):
        if all(isinstance(numero, int) for numero in args):
            return True
        return False
    
    def valid_big_to_zero(*args):
        if not all(numero > 0 for numero in args):
            return False
        return True
    
    def valid_numeric_string(data):
        return data.isnumeric()