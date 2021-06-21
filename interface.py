from kivy.app import App
from kivy.properties import ObjectProperty
from kivy.uix.widget import Widget
from kivy.uix.image import Image


class AppScreen(Widget):

    # Initialize infinite keywords
    name = ObjectProperty(None)  # Or name = self.ids.name.text
    age = ObjectProperty(None)
    height_cm = ObjectProperty(None)
    weight_kg = ObjectProperty(None)
    occupation = ObjectProperty(None)
    gender = ''

    # Configuration
    def slider_angle(self, *args):
        self.angle_tolerance_text.text = f'{round(float(args[1]),2)} °'

    def slider_distance(self, *args):
        self.distance_tolerance_text.text = f'{round(float(args[1]),2)} cm'

    def slider_grid_size(self, *args):
        self.grid_size_text.text = f'{round(float(args[1]),2)} cm'

    def slider_filter_threshold(self, *args):
        self.filter_threshold_text.text = f'{round(float(args[1]),2)}'

    def selected(self, filename):
        try:
            self.ids.my_image.source = filename[0]
            print(filename[0])
        except:
            pass

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

        if self.ids.gender_f.active:
            gender = 'F'
        elif self.ids.gender_m.active:
            gender = 'M'
        else:
            gender = ''

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

        self.ids.diagnostic.text = (f'Hola mi nombre es {name} y tengo {age} de edad\n'
                                    f'Me identifico como {gender}, mido {height_cm} cm\n'
                                    f'Peso {weight_kg} kg, y trabajo como {occupation}\n')

        print(f'Hola mi nombre es {name} y tengo {age} de edad')
        print(f'Me identifico como {gender}, mido {height_cm} cm')
        print(f'Peso {weight_kg} kg, y trabajo como {occupation}')

    def press_clean(self):
        self.name.text = ''
        self.age.text = ''
        self.ids.gender_f.active = False
        self.ids.gender_m.active = False
        self.height_cm.text = ''
        self.weight_kg.text = ''
        self.occupation.text = ''
        self.ids.diagnostic.text = ''
        self.ids.img_anterior.source = ''
        self.ids.img_posterior.source = ''
        self.ids.img_lateral_r.source = ''

    def press_show(self):
        self.ids.img_anterior.source = 'anterior.jpg'
        self.ids.img_posterior.source = 'posterior.jpg'
        self.ids.img_lateral_r.source = 'lateralD.jpg'


class LAM(App):
    title = "Sistema LAM"
    def build(self):
        return AppScreen()


if __name__ == '__main__':
    LAM().run()
