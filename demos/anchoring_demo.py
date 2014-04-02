import random
from uuid import uuid4
from flask import (
  Flask,
  session,
  request,
  redirect,
  url_for,
  render_template_string
)
app = Flask(__name__)

app.config.update(dict(
  DEBUG=True,
  SECRET_KEY='3.14159', # shhhhh
))

from planout.experiment import SimpleExperiment
from planout.ops.random import *

class AnchoringExperiment(SimpleExperiment):
  def assign(self, params, userid):
    params.use_round_number = BernoulliTrial(p=0.5, unit=userid)
    if params.use_round_number:
      params.price = UniformChoice(choices=[100000, 110000, 120000],
        unit=userid)
    else:
      params.price = RandomInteger(min=100000, max=120000, unit=userid)

def money_format(number):
  return "${:,.2f}".format(number)

@app.route('/')
def main():
    # if no userid is defined make one up
    if 'userid' not in session:
        session['userid'] = str(uuid4())

    anchoring_exp = AnchoringExperiment(userid=session['userid'])
    price = anchoring_exp.get('price')

    # need to add a text box and button to submit a bid.
    return render_template_string("""
    <html>
      <head>
        <title>Let's buy a house!</title>
      </head>
      <body>
        <p>
          A lovely new home is going on the market for {{ price }}. <br>
          What will be your first offer?
        </p>
        <form action="/bid" method="GET">
          $<input type="text" length="10" name="bid"></input>
          <input type="submit"></input>
        </form>

      <div><a href="/">Reload without resetting my session ID. I'll get the same offer when I come back.</a></div>
      <div><a href="/reset">Reset my session ID so I get re-randomized into a new treatment.</a></div>
      </body>
    </html>
    """, price=money_format(price))

@app.route('/reset')
def reset():
  session.clear()
  return redirect(url_for('main'))

@app.route('/bid')
def bid():
  bid_string = request.args.get('bid')
  bid_string = bid_string.replace(',', '') # get rid of commas
  try:
    bid_amount = int(bid_string)

    anchoring_exp = AnchoringExperiment(userid=session['userid'])
    anchoring_exp.log_conversion({'bid': bid_amount})

    return render_template_string("""
      <html>
        <head>
          <title>Nice bid!</title>
        </head>
        <body>
          <p>You bid {{ bid }}. We'll be in touch if they accept your offer!</p>
          <p><a href="/">Back</a></p>
        </body>
      </html>
      """, bid=money_format(bid_amount))
  except ValueError:
    return render_template_string("""
      <html>
        <head>
          <title>Bad bid!</title>
        </head>
        <body>
          <p>You bid {{ bid }}. That's not a number, so we probably won't be accepting your bid.</p>
          <p><a href="/">Back</a></p>
        </body>
      </html>
      """, bid=bid_string)


if __name__ == '__main__':
    app.run()
