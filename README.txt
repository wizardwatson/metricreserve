
METRIC RESERVE
by wizardwatson


"A false balance is an abomination to the Lord, 
but a just weight is his delight." - Proverbs 11:1


Metric Reserve is a native Google App Engine application 
designed to provide banking services for whatever currency 
or currencies you want to use.  The fancy-schmancy thing
that makes it different from a typical ledger based payment
or currency system is that it implements an algorithm for
determining graph connectedness and also an algorithm to
suggest reserve distributions in said connected social graph.

To deploy your very own metric reserve application is very
simple for the most part:

1. Get a google account.
2. Create a standard python app engine project (2.7)
	on the google cloud console.
3. Add this repository (or your own copy) to the project.
4. Run the gcloud deploy command for the project.
5. Run the gcloud index creation command.
6. Run the gcloud cron job creation command.
7. Get a google maps api key for the project.
8. As administrator type "settings google_maps_api_key YOURKEY"
	(where "YOURKEY" is your actual key) in the command field
	of the running application. This value isn't stored in
	the code obviously.
	
There are no other outside dependencies.  Currently it 
implements gravatar.com for avatars and uses a google graph
url (unfortunately decprecated) for the QR codes for the 
tickets.  Login uses the standard google "users" api that's 
native to app engine.
	
You can also just run/debug locally with the dev_appserver.py
provided by google app engine.  You still set up the google
maps api key the same way.  The application already has the
python debug library in it, you just need to put the
"pdb.set_trace()" line wherever you want a breakpoint.

The ease of deploying this was why I built it on this
system.  You don't need anything except a web browser and
a google account.  You can even debug/develop on the google
cloud shell.  It's pretty cool.

I'm not a professional python developer by the way, so 
pardon' moi for the sloppy syntax.

LICENSE AND LEGAL

This is just a prototype.  You can of course use it however
you want since I'm making it free, but given that it's banking
software, likely there's all sorts of things to consider like
legal tender laws, FINCEN crawling up your butt, etc. I don't
really know a lot about copyright and whatnot, so I just used
the same license as the old "ripplepay" site by Ryan Fugger.
(https://github.com/rfugger/ripplesite) I spent a lot of time
studying his system, and the algorithms used in this application
were heavily influenced and inspired by his work.  So I figured
would just use the license he used. 

GNU General Public License v2.0 (see LICENSE.txt file)

I.P. is dumb anyway.  If licensing it this way helps keep some 
corporate idiot from thinking he can patent a mathematical 
concept used here then great.

OTHER

Metric Reserve is not a complementary currency, or some kind of
digital currency.  It is a system to allow you to "bank" those
and facilitate payments.  You could just as easily use metric 
reserve to bank bitcoins and dollars and pesos.

I wouldn't call it "Peer-2-Peer" banking, because P2P is really
a technical term.  Bitcoin is P2P "technically" while semantically
it's highly centralized.  Metric reserve is semantically 
decentralized while technically (in this implementation anyway) 
it is centralized. You could make metric reserve a blockchain 
based system if you wanted to.

Anyway, my name's David.  Email is wizardwatson@gmail.com
I'm deploying my own instance at www.metricreserve.com though
not guaranteed to be up there forever.  Instructions to actually
use the application are built into it.  Just click on 
"instructions" from the menu.

There's also some theory and more in-depth boring stuff linked
from the instructions page.

Enjoy.

