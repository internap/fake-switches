from fake_switches.command_processing.base_command_processor import BaseCommandProcessor

class NoPageCommandProcessor(BaseCommandProcessor):
    def __init__(self, enabled):    
        super(NoPageCommandProcessor, self).__init__()
        self.enabled_processor = enabled

    def get_prompt(self):
        return "SSH@%s>" % self.switch_configuration.name

    def delegate_to_sub_processor(self, line):
        processed = self.sub_processor.process_command(line)
        if self.sub_processor.is_done:
            self.is_done = True
        return processed

    def do_enable(self):
        self.write("Password:")
        self.replace_input = ''
        self.continue_to(self.continue_enabling)

    def continue_enabling(self, line):
        self.replace_input = False
        if line == "" or line.encode() in self.switch_configuration.privileged_passwords:
            self.move_to(self.enabled_processor)
        else:
            self.write_line("Error - Incorrect username or password.")