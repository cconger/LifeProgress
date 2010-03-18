import os
import cgi

from datetime import datetime, timedelta
from google.appengine.api import users
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

class ProgressTracker(db.Model):
  """Progress Tracker Model

  MegaStore Model for registering a Tracker for a user."""

  author = db.UserProperty()
  start_date = db.DateTimeProperty(required=True)
  end_date = db.DateTimeProperty(required=True)
  title = db.StringProperty(required=True)
  private = db.BooleanProperty(required=True)

  def percentComplete(self):
    overallDelta = self.timeDeltaToOrdinal(self.end_date - self.start_date) #This should be cached
    currentDelta = self.timeDeltaToOrdinal(datetime.now() - self.start_date)
    return float(currentDelta) / float(overallDelta) * 100.0

  def timeDeltaToOrdinal(self, timeDelta):
    return timeDelta.days * 36400 + timeDelta.seconds
    

class MainPage(webapp.RequestHandler):
  """index.html Controller"""
  def get(self):
    counters = db.GqlQuery("SELECT * FROM ProgressTracker LIMIT 5")
    template_values = { 'counters' : counters }
    path = os.path.join(os.path.dirname(__file__), 'Views/index.html')
    self.response.out.write(template.render(path, template_values))

class UserManager(webapp.RequestHandler):
  """/user/ Controller"""
  def get(self):
    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))

    counters = db.GqlQuery("SELECT * FROM ProgressTracker WHERE author = :1",
                           user)

    template_values = {'userNick' : user.nickname(),
                       'counters' : counters}
    path = os.path.join(os.path.dirname(__file__), 'Views/user.html')
    self.response.out.write(template.render(path, template_values))

class CounterPage(webapp.RequestHandler):
  """/counter/<key> controller"""
  def get(self, counterKey):
    counter = db.get(counterKey)

    template_values = {'counter' : counter}
    path = os.path.join(os.path.dirname(__file__), 'Views/counter.html')
    self.response.out.write(template.render(path, template_values))

class CounterManager(webapp.RequestHandler):
  """/counters controller"""
  def get(self):
    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))

    user_trackers = db.GqlQuery("SELECT * FROM ProgressTracker WHERE author = :1",
                                user)

    self.response.headers['Content-Type'] = 'text/plain'
    self.response.out.write("Current Progress")
    for tracker in user_trackers:
      self.response.out.write("\n%s : %f%%>" % (tracker.title, tracker.percentComplete()))


  def post(self):
    user = users.get_current_user()
    if not user:
      self.redirect(users.create_login_url(self.request.uri))
    
    tracker = ProgressTracker(author=user,
                              title=self.request.get('title'),
                              start_date = datetime.strptime(self.request.get('startDateTime'),
                                                             "%H:%M %m-%d-%Y"),
                              end_date   = datetime.strptime(self.request.get('endDateTime'),
                                                             "%H:%M %m-%d-%Y"),
                              private    = False)

    tracker.put()
    self.redirect(self.request.uri)


application = webapp.WSGIApplication([('/', MainPage),
                                      ('/user', UserManager),
                                      ('/counters', CounterManager),
                                      ('/counter/delete/([^/]+)', CounterPage),
                                      ('/counter/([^/]+)', CounterPage)], debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()


