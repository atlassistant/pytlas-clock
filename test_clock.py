from sure import expect
from pytlas.testing import create_skill_agent
from babel.dates import format_time
from datetime import datetime
import os

class TestClock:

  def test_get_time(self):
    agent = create_skill_agent(os.path.dirname(__file__), lang='en')
    agent.parse('what time is it')
    current_time = datetime.now().time()
    current_formated_time = format_time(current_time, locale= 'en')
    call = agent.model.on_answer.get_call()
    expect(call.text).to.equal('It\'s {}'.format(current_formated_time))
