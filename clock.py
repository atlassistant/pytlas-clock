from pytlas import intent, training, translations, meta, on_agent_created, on_agent_destroyed
from datetime import datetime
from threading import Thread, Timer
import uuid
import dateutil
import geocoder
from timezonefinderL import TimezoneFinder
from pytz import timezone
# This entity will be shared among training data since it's not language specific

locations = """
@[location]
  los angeles
  paris
  rio de janeiro
  tokyo
  london
  tel aviv
  new york
  saint-étienne du rouvray
"""

@training('en')
def en_data(): return """
%[get_time]
  what time is it?
  What's the time?
  Could you give me the time?
  Give me time.
  Time please.
  what time is it in @[location]?
  What's the time in @[location]?

%[start_timer]
  start a timer for @[timer_duration]

@[timer_duration](type=duration)
  3 minutes
  4 seconds
  10 hours
  5s
  34mn
  5h
  6 minutes and 12 seconds
  00:03:00
  7m6s
  13m and 4s 

""" + locations

@training('fr')
def fr_data(): return """
%[get_time]
  Quelle heure est-il?
  Peux-tu me donner l'heure?
  Donne moi l'heure.
  Quelle heure est-il à @[location]?
  Peux-tu me donner l'heure qu'il est à @[location]?
  Donne moi l'heure qu'il est à @[location]?

%[start_timer]
  démarre un minuteur pour @[timer_duration]

@[timer_duration](type=duration)
  3 minutes
  4 secondes
  10 heures
  5s
  34mn
  5h
  6 minutes and 12 secondes
  00:03:00
  7mn6s
  13mn and 4s 

""" + locations

@translations('fr')
def fr_translations(): return {
#  '%I:%M %p':'%H:%M',
  'It\'s {}': 'Il est {}',
  'It\'s {0} in {1}': 'A {1}, il est actuellement {0}',
  'Hummm! It seems {0} doesn\'t exists as city name': 'Hmmmm! Il semble que {0} ne soit pas le nom d\'une ville',
  'Hummm! I encountered an error during {0} information gathering': 'Hmmmm! J\'ai des difficultés pour récuperer les données concernant {0}',
  'Hummm! I can\'t retrieve time zone information of {0}':'Hmmmm! Je ne parviens pas à récuperer les données de fuseau horaire pour {0}',
  'Times up' : 'Le temps est écoulé',
  'What is the duration?' : 'Quelle est la durée',
  'A timer has been started for {0:02}:{1:02}:{2:02} from now ({3})' : 'Un minuteur d\'une durée de {0:02}:{1:02}:{2:02} vient d\'être démarré ({3})' 
}

@meta()
def help_meta(_): return {
  'name': _('clock'),
  'description': _('Give you time and make your boiled eggs a success'),
  'author': 'Jean-Michel LEKSTON',
  'version': '1.0.0',
  'homepage': 'https://github.com/atlassistant/pytlas-clock',
}


@intent('get_time')
def on_clock(req):
  city = req.intent.slot('location').first().value
  if not city:
    current_time = datetime.now().time()
    #resp = req._('It\'s {}').format(current_time.strftime(req._('%I:%M %p')))
    resp = req._('It\'s {}').format(req._d(current_time, time_only=True))
    req.agent.answer(resp)
    return req.agent.done()
  else:
    try:
      g = geocoder.osm(city)
      if not g:
        resp = req._('Hummm! It seems {0} doesn\'t exists as city name').format(city)
        req.agent.answer(resp)
        return req.agent.done()
    except:
        resp = req._('Hummm! I encountered an error during the city information gathering')
        req.agent.answer(resp)
        return req.agent.done()
    tf = TimezoneFinder()
    tzStr = tf.timezone_at(lng=g.lng, lat=g.lat)
    if tzStr == '':
        resp = req._('Hummm! I can\'t retrieve time zone information of {0}').format(city)
        req.agent.answer(resp)
        return req.agent.done()
    tzObj = timezone(tzStr)
    current_time = datetime.now(tzObj)
    #resp = req._('It\'s {0} in {1}').format(current_time.strftime(req._('%I:%M %p'), city)
    resp = req._('It\'s {0} in {1}').format(req._d(current_time, time_only=True), city)
  req.agent.answer(resp)
  return req.agent.done()


agents = {}

@on_agent_created()
def when_an_agent_is_created(agt):
  # On conserve une référence à l'agent
  global agents
  agents[agt.id] = {"agent":agt,"timers":{}}

@on_agent_destroyed()
def when_an_agent_is_destroyed(agt):
  # On devrait clear les timers pour l'agent à ce moment là
  global agents
  if agt.id in agents:
    for timer_uuid in agents[agt.id]["timers"]:
      try:
        agents[agt.id]["timers"][timer_uuid].cancel()
      except:
        pass
  agents.pop(agt.id,None)


def timer_callback(timer_uuid, agt_id, translate):
  global agents
  try:
    agents[agt_id]["agent"].answer(translate('Times up'))
    agents[agt_id]["timers"].pop(timer_uuid, None)
  except:    
    pass

@intent('start_timer')
def on_start_timer(req):
  global agents
  duration_text = req.intent.slot('timer_duration').first().value 
  if  duration_text == None:
    return req.agent.ask('timer_duration', req._('What is the duration?'))
  relative_delta = req.intent.slot('timer_duration').first().value
  timeup_datetime = datetime.now() + relative_delta
  duration = timeup_datetime - datetime.now()
  duration_seconds = round(duration.total_seconds())
  timer_uuid = uuid.uuid4()
  timer = Timer(duration_seconds, timer_callback, args=(timer_uuid, req.agent.id,req._))
  agents[req.agent.id]["timers"][timer_uuid] = timer  
  timer.start()
  current_time = datetime.now().time()
  req.agent.answer(req._('A timer has been started for {0:02}:{1:02}:{2:02} from now ({3})').format(relative_delta.hours, relative_delta.minutes, relative_delta.seconds, req._d(current_time, time_only=True) ))
  return req.agent.done()
