import yaml
import sqlite3

class MyClass:
    def __init__(self):
        self.cfg_data = None
        self.text = None

    def config(self):
        # Load YAML data from the file
        with open('./cfg/appsettings.yml', 'r') as arquivo:
            self.cfg_data = yaml.load(arquivo, Loader=yaml.FullLoader)

    def select_text(self, alias):
        self.config()
        language = self.cfg_data['user_cfg']['language']
        conn = sqlite3.connect('./SQLite/imc_bmi.db')
        cursor = conn.cursor()
        cursor.execute(f'''SELECT "{language}" FROM language WHERE alias = ?''', (alias,))
        result = cursor.fetchone()
        if result:
            self.text = result[0]  # Extract the text from the tuple
            return self.text
        else:
            return None  # Return None if no match for the alias
        
    def select_units(self, alias, table):
        self.config()
        unit = self.cfg_data['user_cfg']['unit']
        conn = sqlite3.connect('./SQLite/imc_bmi.db')
        cursor = conn.cursor()
        cursor.execute(f'''SELECT "{unit}" FROM {table} WHERE alias = ?''', (alias,))
        result = cursor.fetchone()
        if result:
            self.text = result[0]  # Extract the text from the tuple
            return self.text
        else:
            return None  # Return None if no match for the alias


if __name__ == '__main__':    
    # Instantiate the object
    obj = MyClass()
    # Configure the object
    # obj.config()
    # Call the method select_units
    result = obj.select_units('weight', 'units')
    print(result)