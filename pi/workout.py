import time

class Workout:
    timeout : int
    threshold_v : tuple[float,float,float]
    threshold_m : tuple[int,int,int]
    workout : str
    init_time : int
    rep_time : list[ int ]
    count : int
    select : tuple[int,int]

    def __init__(self, workout):
        self.workout = workout
        self.init_time = time.time()
        self.rep_time = []
        self.count = 0
        self.__assign()

    def __assign(self):
        if self.workout == 'Seated Cable Rows' or self.workout == 'Rows':
            self.select = (0,2) # x-axis for velocity, z-axis for mag
            self.threshold_v = (0.325,0,0)
            self.threshold_m = (0,0,-40)
            self.timeout = 1.25
        elif self.workout == "Lat Pulldowns":
            self.select = (0,0)
            self.threshold_v = (0.75,0,0)
            self.threshold_m = (0,0,-40)
            self.timeout = 1.00
        
    def __sign_v(self):
        if (self.threshold_v[self.select[0]] < 0):
            return -1
        else:
            return 1
        
    def __sign_m(self):
        if (self.threshold_m[self.select[1]] < 0):
            return -1
        else:
            return 1

    def update(self,velocity,mag):
        time.time()
        sel = self.select
        if (velocity[sel[0]] * self.__sign_v() > self.threshold_v[sel[0]] or mag[sel[1]] * self.__sign_m() > self.threshold_m[sel[1]] * self.__sign_m()):
            current_time = time.time() - self.init_time
            if (len(self.rep_time) == 0 or current_time - self.rep_time[-1] > self.timeout):
                self.count += 1
                self.rep_time.append(current_time)
                return (True,self.count) #Returns true if rep is counted, and number of reps so far
            
            else : 
                return (False,None) #Returns false if rep is not counted, and None
        else : 
            return (False,None)
    
    def get_data(self):
        return (self.workout,self.count,self.rep_time)#Reutrns workout name, count, and rep times