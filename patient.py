class Patient:

    def __init__(self):

        self.name = input("Nombre: ")
        self.name = self.name.strip().title()
        if self.name == '':
            self.name = 'Anónimo'

        try:
            self.age = int(input("Edad: "))
            while self.age <= 0:
                print('Ingrese un valor válido > 0')
                self.age = int(input("Edad: "))
        except ValueError:
            print('Error en ingreso de edad')
            self.age = None

        self.gender = input("Género (M/F): ")
        self.gender = self.gender.strip().upper()
        if not (self.gender == 'M' or self.gender == 'F'):
            print('Error al ingresar género')
            self.gender = None

        try:
            self.height_cm = float(input("Altura en cm: "))
            while self.height_cm <= 0:
                print('Ingrese un valor válido > 0')
                self.height_cm = float(input("Altura en cm: "))
        except ValueError:
            print('Error en ingreso de altura')
            self.height_cm = None

        try:
            self.weight_kg = float(input("Peso en Kg: "))
            while self.weight_kg <= 0:
                print('Ingrese un valor válido > 0')
                self.weight_kg = float(input("Peso en Kg: "))
        except ValueError:
            print('Error en ingreso de peso')
            self.weight_kg = None

        self.occupation = input("Ocupación: ")
        self.occupation = self.occupation.strip().title()

    def get_name(self):
        return self.name

    def get_age(self):
        return self.age

    def get_gender(self):
        return self.gender

    def get_weight_kg(self):
        return self.weight_kg

    def get_height_cm(self):
        return self.height_cm

    def get_occupation(self):
        return self.occupation
