import ui
from string import Template
from pathlib import Path
from functools import partial

import winds

import results
import config


default_config = config.Config()

# TODO: func to convert degrees to slider val and back


def initialize_wind_calculator(config):
    """
    Return a `winds.WindCalculator` instance with the default max values
    set per the `config` parameter
    """
    wind_calc = winds.WindCalculator()
    wind_calc.max_ldg_tailwind = config.max_tailwind_landing
    wind_calc.max_to_tailwind = config.max_tailwind_takeoff
    wind_calc.runway_heading = 180
    return wind_calc


class WindCalcView(ui.View): 
    WIND_INFO_LABEL_TEMPLATE = Template('Winds: ${wind_dir}° @ ${wind_speed} kts')
    RUNWAY_DIR_LABEL_TEMPLATE = Template('Runway HDG: ${runway_dir}°')
 
    def __init__(self):
        self.wind_calculator = initialize_wind_calculator(default_config)
        self.wind_dir, self.wind_speed = 180, 10
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
        
        self.calculate_button = self['calculate_button']
        self.calculate_button.action = self.calculate_button_pressed
        self.calculation_type_controller = self['calculation_type_controller']
        
        self.results_nav_view = self['results_nav_view']
         
        self.update_wind_info_label()
        self.update_runway_dir_label()
        self.snap_slider_to_prev_val(self.runway_wind_controller)
        
    def update_wind_info_label(self):
        kwargs = {'wind_dir': f'{self.wind_dir:.1f}', 'wind_speed': f'{self.wind_speed:.1f}'}
        self.wind_info_label.text = self.WIND_INFO_LABEL_TEMPLATE.safe_substitute(**kwargs)
        
    def update_runway_dir_label(self):
        val = self.wind_calculator.runway_heading
        self.runway_dir_label.text = self.RUNWAY_DIR_LABEL_TEMPLATE.safe_substitute(runway_dir=f'{val:.0f}')
        
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
        
    def calculate_button_pressed(self, button):
        controller = self.calculation_type_controller
        funcs = {
            'GRID TO': (self.do_grid_calculation, 'takeoff'),
            'GRID LDG': (self.do_grid_calculation, 'landing')
        }
        func, *args = funcs.get(
            controller.segments[controller.selected_index],
            (None, None)
            )
        if func is None:
            # TODO: handle no func
            return
        func(*args)
   
    # TODO: distinguish between TO/LDG tailwind limitations     
    def do_grid_calculation(self, phase):
        """
        Create and push the results view
        """
        phases = {
            'takeoff': self.wind_calculator.max_to_tailwind,
            'landing': self.wind_calculator.max_ldg_tailwind
        }
        if phase not in ['takeoff', 'landing']:
            raise ValueError('phase must be "takeoff" or "landing"')
        grid = winds.max_wind_grid(
            self.wind_dir,
            7,
            phases[phase],
            runway_hdg=self.wind_calculator.runway_heading
            )
        view = results.make_grid_view(grid)
        self.results_nav_view.push_view(view)
        
               
    
if __name__ == '__main__':

    view = ui.load_view()
    
    wind_calc_view = view['wind_calc_view']

    view.present('fullscreen')

    
    
