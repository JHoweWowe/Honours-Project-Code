class WebScrapperHelper():

    # Assuming time_str is consistent - converts time String into Integer (mins)
    def convert_timeStr_to_Mins(self, time_str):
        mins = 0
        time_str_array = time_str.split(" ")

        if (len(time_str_array) == 4): # Eg: "1 hr 15 mins"
            mins += (int(time_str_array[0]) * 60) + int(time_str_array[2])

        elif (len(time_str_array) == 2): # Eg: "30 mins" OR "1 hr"
            if (time_str_array[1] == 'hr' or time_str_array[1] == 'hrs'):
                mins += (int(time_str_array[0]) * 60)
            elif (time_str_array[1] == 'mins'):
                mins += (int(time_str_array[0]))

        return mins

helper = WebScrapperHelper()
mins = helper.convert_timeStr_to_Mins("1 hr")
print(mins)