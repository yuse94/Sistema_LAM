from kivy.app import App
from kivy.properties import ObjectProperty
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout


class AppScreen(Widget):
    pass


class DataBox(BoxLayout):
    # Initialize infinite keywords

    name = ObjectProperty(None)  # Or name = self.ids.name.text
    age = ObjectProperty(None)
    gender = ObjectProperty(None)
    height_cm = ObjectProperty(None)
    weight_kg = ObjectProperty(None)
    occupation = ObjectProperty(None)

    def press_load(self):

        if not self.name.text:
            name = 'Anónimo'
        else:
            name = self.name.text.strip().title()

        if not self.age.text:
            age = None
        else:
            try:
                age = int(self.age.text)
            except ValueError:
                age = None

        if not self.gender.text:
            gender = None
        else:
            gender = self.gender.text

        if not self.height_cm.text:
            height_cm = None
        else:
            try:
                height_cm = float(self.height_cm.text)
            except ValueError:
                height_cm = None

        if not self.weight_kg.text:
            weight_kg = None
        else:
            try:
                weight_kg = float(self.weight_kg.text)
            except ValueError:
                weight_kg = None

        if not self.occupation.text:
            occupation = None
        else:
            occupation = self.occupation.text.strip().title()


        print(f'Hola mi nombre es {name} y tengo {age} de edad')
        print(f'Me identifico como {gender}, mido {height_cm} cm')
        print(f'Peso {weight_kg} kg, y trabajo como {occupation}')

    def press_clean(self):
        self.name.text = ''
        self.age.text = ''
        self.gender.text = ''
        self.height_cm.text = ''
        self.weight_kg.text = ''
        self.occupation.text = ''

class ImagesBox(BoxLayout):
    None


class DiagnosticBox(BoxLayout):
    None


class LAM(App):
    title = "Sistema LAM"
    def build(self):
        return AppScreen()


if __name__ == '__main__':
    LAM().run()
