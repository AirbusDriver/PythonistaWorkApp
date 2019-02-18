import ui
import winds
from string import Template



def wind_dir_slider_moved(slider):
    val = int((slider.value * 36) % 36)
    val *= 10
    wind_dir_label.text = WIND_DIR_TEMPLATE.substitute(wind_dir=f'{val:3.0f}')
    
class WindCalcView(ui.View):
    
    WIND_INFO_LABEL_TEMPLATE = Template('Winds: ${wind_dir}° @ ${wind_speed} kts')
    RUNWAY_DIR_LABEL_TEMPLATE = Template('Runway HDG: ${runway_dir}°')

    
    def __init__(self):
        self.wind_calculator = winds.WindCalculator()
        self.wind_dir, self.wind_speed = 0, 0
        self._last_wind_dir_slider_val = .5
        self._last_runway_slider_val = .5

    
    def did_load(self):
        self.wind_info_label = self['wind_info_label']
        self.wind_dir_slider = self['wind_dir_slider']
        self.wind_dir_slider.continuous = True
        self.wind_dir_slider.action = self.dir_slider_moved
        self.wind_speed_slider = self['wind_speed_slider']
        self.wind_speed_slider.action = self.wind_speed_slider_moved
        self.wind_speed_slider.continuous = True
        self.runway_dir_label = self['runway_dir_label']
        
        self.runway_wind_controller = self['runway_wind_controller']
        self.runway_wind_controller.action = self.snap_slider_to_prev_val

        
        self.update_wind_info_label()
        self.update_runway_dir_label()
        
    def update_wind_info_label(self):
        kwargs = {'wind_dir': f'{self.wind_dir:.1f}', 'wind_speed': f'{self.wind_speed:.1f}'}
        self.wind_info_label.text = self.WIND_INFO_LABEL_TEMPLATE.safe_substitute(**kwargs)
        
    def snap_slider_to_prev_val(self, wind_rwy):
        val = wind_rwy.segments[wind_rwy.selected_index]
        prev = 'WIND' if val == 'RWY' else 'RWY'
        slider_val = self.wind_dir_slider.value
        if prev == 'WIND':
            self._last_wind_dir_slider_val = slider_val
            self.wind_dir_slider.value = self._last_runway_slider_val
        else:
            self._last_runway_slider_val = slider_val
            self.wind_dir_slider.value = self._last_wind_dir_slider_val

        
    def update_runway_dir_label(self):
        val = self.wind_calculator.runway_heading
        self.runway_dir_label.text = self.RUNWAY_DIR_LABEL_TEMPLATE.safe_substitute(runway_dir=f'{val:.0f}')
    
    def dir_slider_moved(self, sender):

        def update_wind(slider):
            INCREMENTS = 10
            val = int((slider.value * (360 / INCREMENTS)) % 360) * INCREMENTS
            self.wind_dir = val
            self.update_wind_info_label()
            
        def update_runway(slider):
            val = int((slider.value * 360) % 360)
            self.wind_calculator.runway_heading = val
            self.update_runway_dir_label()
            
            
        func = {
            'RWY': update_runway,
            'WIND': update_wind,
        }.get(self.runway_wind_controller.segments[self.runway_wind_controller.selected_index])
        func(sender)
        
        
    def wind_speed_slider_moved(self, sender):
        MAX = 100
        val = sender.value * MAX
        self.wind_speed = int(val)
        self.update_wind_info_label()
        
        
    
if __name__ == '__main__':

    view = ui.load_view()
    
    wind_calc_view = view['wind_calc_view']

    view.present('fullscreen')

    
    
