"""
--------------------------------------------------------------------------
Morse Code Transceiver
--------------------------------------------------------------------------
License:   
Copyright 2024 - Edwin Low

Redistribution and use in source and binary forms, with or without 
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this 
list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, 
this list of conditions and the following disclaimer in the documentation 
and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors 
may be used to endorse or promote products derived from this software without 
specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE 
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE 
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL 
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR 
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER 
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, 
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
--------------------------------------------------------------------------

Hardware Components:
  - Arcade Button
  - Pushbuttons
  - LED
  - Buzzer
  - Potentiometer
  - SPI screen
  - Wifi

"""

import time
import threading
import buzzer
import led
import potentiometer
import spi_screen
import threaded_button


# Constant for aligning texts on the SPI screen
CENTER = 4


class Morse():
    
    # Morse code representation for letters and numbers
    morse_code_dict = {
        '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E', '..-.': 'F',
        '--.': 'G', '....': 'H', '..': 'I', '.---': 'J', '-.-': 'K', '.-..': 'L',
        '--': 'M', '-.': 'N', '---': 'O', '.--.': 'P', '--.-': 'Q', '.-.': 'R',
        '...': 'S', '-': 'T', '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X',
        '-.--': 'Y', '--..': 'Z', '-----': '0', '.----': '1', '..---': '2',
        '...--': '3', '....-': '4', '.....': '5', '-....': '6', '--...': '7',
        '---..': '8', '----.': '9'
    }
    
    arcade_button = None
    mode_button = None
    control_button = None
    delete_button = None
    led = None
    buzzer = None
    potentiometer = None
    current_input = None
    translated_text = None
    accept_input = None
    spi_display = None
    
    def __init__(self, arcade_button_pin="P2_2", mode_button_pin="P2_4", 
                    control_button_pin="P2_6", delete_button_pin="P2_8", led_pin="P2_10", buzzer_pin="P1_36",
                    potentiometer_pin="P1_19"):
        # Initialize button variables
        self.arcade_button = threaded_button.ThreadedButton(arcade_button_pin)
        self.mode_button = threaded_button.ThreadedButton(mode_button_pin)
        self.control_button = threaded_button.ThreadedButton(control_button_pin)
        self.delete_button = threaded_button.ThreadedButton(delete_button_pin)
        
        
        # Setting up the arcade button callbacks
        self.arcade_button.set_on_press_callback(self.arcade_button_pressed)
        self.arcade_button.set_on_release_callback(self.arcade_button_released)
        
        # Setting up the control button callbacks
        self.control_button.set_on_press_callback(self.control_button_pressed)
        self.control_button.set_on_release_callback(self.control_button_released)
        
        # Setting up the delete button callback
        self.delete_button.set_on_press_callback(self.delete_last_character)
        
        # current_input stores what the user enters in Morse code. 
        # translated_text stores the translated Morse code for transmission later.
        self.current_input = ""
        self.translated_text = ""
        
        # User can't input before scaling pause time.
        self.accept_input = False
        
        # Setting default pause times between letters and words
        self.pause_between_letters = 3.0
        self.pause_between_words = 7.0
        
        # Setting up LED, buzzer, and potentiometer
        # The LED is the arcade button's built-in LED
        self.led = led.LED(led_pin)
        self.buzzer   = buzzer.Buzzer(buzzer_pin)
        self.potentiometer = potentiometer.Potentiometer(potentiometer_pin)
        
        # Timestamp of the last button release or space added
        self.last_activity_time = None
        
        # Start the monitoring thread for detecting pause times between buttons
        self.monitor_thread = threading.Thread(target=self.monitor_input, daemon=True)
        self.monitor_thread.start()
        
        
        # # Setting up the SPI Screen
        self.spi_display = spi_screen.SPI_Display()
        
    
    def welcome(self):
        "Display welcome message alongside LED and buzzer"
        self.spi_display.image("Welcome.png")
        time.sleep(5)
        
    
    def scale_pause_time(self, pot_value, original_pause):
        """Scaling pause times with potentiometer."""
        min_scale = 0.5  # Pause times can go as low as half the original time.
        max_scale = 2.0  # Pause times can go up to twice the original time.
        
        # Map potentiometer value from 0-4095 to min_scale-max_scale
        scale_factor = (pot_value / 4095) * (max_scale - min_scale) + min_scale
        
        return original_pause * scale_factor

    
    def configure_pause_time(self):
        """Allows the user to scale the pause times by turning the potentiometer."""
        
        self.spi_display.image("Scale.png")
        time.sleep(5)
        self.spi_display.blank()
        
        while not self.accept_input:
            # Testing: print out values and scaled time
            # Note that pot_value of around 1365 gives the default 3 seconds and 7 seconds
            # User can keep on scaling the time until they press control_button
            pot_value = self.potentiometer.get_value()
            self.pause_between_letters = round(self.scale_pause_time(pot_value, 3), 1)
            self.pause_between_words = round(self.scale_pause_time(pot_value, 7), 1)
            print("Pot value   = {0}".format(pot_value))
            print("Pause between letters = {0} s".format(self.pause_between_letters))
            print("Pause between words = {0} s".format(self.pause_between_words))
            
            self.spi_display.text(["Pause between letters: ", str(self.pause_between_letters),
                                  "Pause between words: ", str(self.pause_between_words)], 
                                  fontsize=200, justify=CENTER, align=CENTER)
        
            time.sleep(2)
            
            if self.accept_input:
                break
        
        
    
    # Use control_button (green) to start/stop input or transmit message
    def control_button_pressed(self):
        """Callback function for when the control_button is pressed."""
        pass
    
    def control_button_released(self):
        """Callback function for when the control_button is released."""
        press_duration = self.control_button.get_last_press_duration()
        if press_duration < 3:
            self.accept_input = not self.accept_input  # Toggle input acceptance
            self.last_activity_time = time.time() # Reset the timer for detecting letter/word
            self.current_input = "" # Reset the Morse code input
            if self.accept_input:
                print("Start inputting Morse code. Press green button to stop.")
                self.spi_display.image("Start.png")
                # Reset time in case user hasn't started inputting anything after pause_between_letters elapsed
                self.reset_time() 
            else:
                print("Stopped inputting Morse code. Press green button to start. Long press 3 seconds to transmit message.")
                self.spi_display.image("Stop.png")
        else:
            if self.accept_input:
                # Can only transmit when input is stopped
                print("Can't transmit message. Press green button to stop before transmitting.")
                self.spi_display.image("TransmitFail.png")
            else:
                if not self.translated_text:
                    print("No message entered. Input message before transmitting.")
                    self.spi_display.image("NoMessage.png")
                else:
                    # Transmit the Morse code
                    print(f"Transmitting message: {self.translated_text}")
                    self.buzzer.play(440, 1, False)
                    self.buzzer.stop()
                    self.current_input = ""  # Reset the Morse code input
                    self.translated_text = "" # Reset translated text
                    self.last_activity_time = time.time() # Reset the timer for detecting the end of a letter or word
                    print("Message transmitted. Press green button to start inputting new message.")
                    self.spi_display.image("Transmit.png")
    
    
    # Use arcade_button to input Morse code        
    def arcade_button_pressed(self):
        """Callback function for when the arcade_button is pressed."""
        pass

    def arcade_button_released(self):
        """Callback function for when the arcade_button is released."""
        if self.accept_input:
            press_duration = self.arcade_button.get_last_press_duration()
            if press_duration <= 0.5:
                self.current_input += '.'
                self.led.on()
                self.buzzer.play(440, 0.1, False)
            else:
                self.current_input += '-'
                self.led.on()
                self.buzzer.play(440, 0.3, False)
            
            self.buzzer.stop()
            self.led.off()
            print(f"current input: {self.current_input}")
            # Reset the timer for detecting the end of a letter or word
            self.last_activity_time = time.time()
            

    def reset_time(self):
        """
        Reset the timer for detecting the end of a letter or word.
        
        Accounts for cases where the user hasn't inputted anything within the duration of pause_between_letters.
        If that is the case, whatever the user enters will be detected as either an E (.) or a T (-).
        Without this function, the system won't check for anything pass the first press on the arcade button.
        (e.g. Let pause_between_letters = 6s and pause_between_words = 14s. After pressing control_button and 
        prompting "Start inputting Morse code", the user doesn't input anything before 6 seconds elapsed. When
        the user tries to input something after 6 seconds, the first thing they input (. or -) will be translated
        immediately as an E or T. Everything they try to input after the first thing will be counted towards the 
        next letter. Adding the self.reset_time() function prevents this from happening.
        """
        self.last_activity_time = time.time()
        while True:
            if (time.time() - self.last_activity_time) > self.pause_between_letters:
                self.last_activity_time = time.time()
                # print("Time reset.")
            if self.current_input:
                break
        
    def monitor_input(self):
        """Continuously monitor the timing to handle translation and space insertion."""
        while True:
            time.sleep(0.1)
            if not self.accept_input or self.last_activity_time is None:
                continue
            
            current_time = time.time()
            if self.current_input and (current_time - self.last_activity_time >= self.pause_between_letters):
                self.check_and_translate_code()

            if (current_time - self.last_activity_time >= self.pause_between_words - self.pause_between_letters):
                if self.translated_text and not self.translated_text.endswith(' '):
                    self.translated_text += ' '
                    print(f"Space added. Translated text: '{self.translated_text}'")
                    self.last_activity_time = time.time()  # Reset activity time after adding a space
                    self.reset_time()
            
    
    def check_and_translate_code(self):
        """Translate Morse code to text and handle the current input.
        
           Note that the user shouldn't input anything if the time elapsed is greater than pause_between_letters.
           For example, let pause_between_letters = 6s and pause_between_words = 14s. 6 seconds after the user's
           last input, the system will translate the code into letter. It will take another 14 - 6 = 8 seconds
           before the system adds a space after the letter. Within these 8 seconds, the user can input letters
           normally as long as they do it before 6 seconds elapsed. If they didn't input anything and try to 
           input code between 6 and 8 seconds, there will be a bug. Whatever they input will be translated as 
           either an E (.) or a T (-). The system figures that another pause_between_letters duration has passed,
           and whatever being inputted is just the letter itself. 
           
           This is the same issue that reset_time(self) above tried to solve. However, calling reset_time(self) in 
           this case means resetting the whole timing, so it's impossible for a space to ever be added. I tried to 
           implement another function that prevents this, but it created more bugs in other parts of the code. 
        """
        if self.accept_input:
            if self.current_input in Morse.morse_code_dict:
                letter = Morse.morse_code_dict[self.current_input]
                print(f"Translated letter: {letter}")
                self.translated_text += letter  # Add the translated letter/number to the string
                print(f"Translated text: {self.translated_text}")
            else:
                print("Invalid Morse code. Enter again.")
            self.current_input = ''  # Reset input for the next character
            self.last_activity_time = time.time()  # Update last activity time after translation
    
            # After handling the current input, decide on accepting new input
        
            print("Ready for next letter.")
            
        
            
            
    
    # Use delete_button to delete incorrect letters
    def delete_last_character(self):
        if self.translated_text:
            self.translated_text = self.translated_text[:-1]
            print(f"Last character deleted. Translated text: '{self.translated_text}'")
            
            # Update the last activity timestamp to reset timing assumptions
            self.last_activity_time = time.time()
    
    def transmit_message(self):
        # Needs to be changed for future versions of this project
        pass
    
    
    def start(self):
        """Starts the threaded buttons."""
        self.control_button.start()
        self.arcade_button.start()
        self.delete_button.start()
    
    def cleanup(self):
        """Cleans up the buttons and threads upon exit."""
        self.control_button.cleanup()
        self.arcade_button.cleanup()
        self.delete_button.cleanup()
        self.buzzer.cleanup()
        self.led.cleanup()
        self.spi_display.blank()
        exit()
    
    
    
# ------------------------------------------------------------------------
# Main script
# ------------------------------------------------------------------------

if __name__ == '__main__':

    print("Program Start")
    
    morse = Morse()
    
    morse.spi_display.blank() # Make the screen blank
    morse.welcome() # Display welcome message
    morse.start()  # Start monitoring the buttons
    morse.configure_pause_time()
    
    try:
        while True:
            time.sleep(0.1)  # Keep the main program alive
    except KeyboardInterrupt:
        morse.cleanup()
        
    print("Program Complete")
    
    