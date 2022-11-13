from fake_switches.command_processing.base_command_processor import BaseCommandProcessor

class DefaultCommandProcessor(BaseCommandProcessor):
    def __init__(self, no_page):    
        super(DefaultCommandProcessor, self).__init__()
        self.no_page_processor = no_page

    def get_prompt(self):
        return "SSH@%s>" % self.switch_configuration.name

    def delegate_to_sub_processor(self, line):
        processed = self.sub_processor.process_command(line)
        if self.sub_processor.is_done:
            self.is_done = True
        return processed

    def do_no_page(self, *args):
        self.write_line("No Page enabled!")
        self.move_to(self.no_page_processor)