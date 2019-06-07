_RCAM_CROSSWINDS = {
    6: 38,
    5: 38,
    4: 29,
    3: 25,
    2: 20,
    1: 15
}

_MAX_TAILWIND_TO = 15
_MAX_TAILWIND_LDG = 10


class Config:
    _RCAM_CROSSWINDS = _RCAM_CROSSWINDS.copy()
    _MAX_TAILWIND_TO = _MAX_TAILWIND_TO
    _MAX_TAILWIND_LDG = _MAX_TAILWIND_LDG
    
    def get_max_crosswind(self, rcam=5):
        """
        Return the maximum crosswind allowed for a given RCAM value
        
        params
        ------
        rcam (int): int representing the RCAM lookup value
        """
        try:
            return self._RCAM_CROSSWINDS[int(rcam)]
        except KeyError:
            raise KeyError(f'{rcam} is not a valid RCAM value... available values are '
            f'{self.RCAM_CROSSWINDS.keys()}')
            
    @property
    def max_tailwind_takeoff(self):
        return self._MAX_TAILWIND_TO
        
    @property
    def max_tailwind_landing(self):
        return self._MAX_TAILWIND_LDG

