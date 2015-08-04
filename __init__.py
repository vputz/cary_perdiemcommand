from cary.carycommand import CaryCommand, CaryAction
import datetime
from cary_perdiemcommand.perdiem_database import PerdiemDatabase
from jinja2 import Environment, FileSystemLoader


def formatted_reply(locstring_filename, db_filename, location, template):

    pd = PerdiemDatabase(locstring_filename, db_filename)
    pd_query = pd.perdiem_query(location)
    return template.render(pd_query)


class PerDiemCommand(CaryCommand):

    @property
    def name(self):
        return "perdiem"

    @property
    def description(self):
        return "Retrieve a per diem quote"

    @property
    def required_attachments(self):
        return ["location in body of message"]

    def _create_action(self, parsed_message):
        return PerDiemAction(parsed_message)


class PerDiemAction(CaryAction):

    def __init__(self, parsed_message):
        super().__init__(parsed_message)

    def validate_command(self):
        """
        The echo command always succeeds.
        """
        self.command_is_valid = True

    def search_line(self):
        return self._message.body.split("\n", 1)[0]

    def execute_action(self):
        self.environment = Environment(loader=FileSystemLoader(
            self.config['TEMPLATE_PATH']
            ))
        self._output_filenames = []
        self._perdiem_text_plain = formatted_reply(
            self.config['LOCSTRING_FILENAME'],
            self.config['DB_FILENAME'],
            self.search_line(),
            self.environment.get_template('plaintext_template.txt')
        )
        self._perdiem_text_html = formatted_reply(
            self.config['LOCSTRING_FILENAME'],
            self.config['DB_FILENAME'],
            self.search_line(),
            self.environment.get_template('html_template.html')
        )

    @property
    def response_subject(self):
        return "Your per diem request"

    @property
    def response_body(self):
        return self._perdiem_text_plain

    @property
    def response_body_html(self):
        return self._perdiem_text_html

if __name__ == "__main__":
    print(formatted_reply("/tmp/locstrings.csv",
                          "/tmp/perdiem.json",
                          "Brugges, belgium",
                          html_perdiem_template))
