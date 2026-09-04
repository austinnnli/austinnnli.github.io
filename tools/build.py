#!/usr/bin/env python3
"""Static site generator for Austin Li's portfolio.

Every page (index, gallery, and the six standalone project pages) is rendered
from the single PROJECTS list below, so content only ever lives in one place.
Run:  python3 build.py
"""
import os, html, shutil, textwrap
from PIL import Image

_DIMS = {}
def dims(name):
    if name not in _DIMS:
        try:
            with Image.open(os.path.join(OUT, 'assets/img', name + '.webp')) as im:
                _DIMS[name] = im.size
        except Exception:
            _DIMS[name] = None
    d = _DIMS[name]
    return ' width="%d" height="%d"' % d if d else ''

def aspect(name):
    dims(name)
    d = _DIMS.get(name)
    return (d[0] / d[1]) if d else 1.0

OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # repo root

SITE = {
    'name':     'Austin Li',
    'name_up':  'Austin Li',
    'role':     'Mechatronics Engineer',
    'email':    'austincheungli@gmail.com',
    'phone':    '236-838-2903',
    'phone_href': '+12368382903',
    'linkedin': 'https://www.linkedin.com/in/austin-c-li/',
    'github':   'https://github.com/austinnnli',
    'resume':   'assets/resume.pdf',
    'note':     'I am currently open to Winter/Spring 2027 co-op opportunities, '
                'contact me so we can work together.',
    'lede':     'Waterloo Mechatronics Engineering student, curious to learn how things work, '
                'passionate to make them better.',
    'url':      'https://austinnnli.github.io',
}

# --------------------------------------------------------------------------- #
#  content helpers — each block is a small dict the renderer knows how to draw
# --------------------------------------------------------------------------- #
def h(t):        return {'k': 'h',    'text': t}
def p(t):        return {'k': 'p',    'text': t}
def lead(t):     return {'k': 'lead', 'text': t}
def img(src, alt, cap=None, narrow=False):
    return {'k': 'img', 'src': src, 'alt': alt, 'cap': cap, 'narrow': narrow}
def pair(a, b):  return {'k': 'pair', 'items': [a, b]}
def row(*it):    return {'k': 'row', 'items': list(it)}   # equal heights, native aspects
def stack(*it):  return {'k': 'stack', 'items': list(it)}
def video(src, poster, alt, cap=None, replay=False, speed=False):
    return {'k': 'video', 'src': src, 'poster': poster, 'alt': alt, 'cap': cap,
            'replay': replay, 'speed': speed}
def steps(a, b): return {'k': 'steps', 'items': [a, b]}
def cad(model, cap=None):
    return {'k': 'cad', 'model': model, 'cap': cap}

# --------------------------------------------------------------------------- #
PROJECTS = [
{
  'slug':  'pmsm-hub-motor',
  'brief': "A permanent-magnet synchronous hub motor I built from scratch &mdash; stator, windings, rotor and magnets &mdash; designed specifically for field oriented control, and destined to drive a DIY OneWheel.",
  'title': 'PMSM OneWheel Hub Motor',
  'blurb': 'A permanent-magnet synchronous hub motor designed and built from scratch, '
           'specced end to end for field oriented control.',
  'cover': 'cover-motor',
  'tile':  't-motor',
  'body': [
    img('p1-cover', 'Hand-wound stator of the PMSM hub motor'),
    h('Objective'),
    p('I have always been intrigued by motors (electric motors in particular), the ability to '
      'turn electricity into motion seems magical, and yet the way motors are so ubiquitous today '
      'turn them into this seemingly simple thing which we take for granted. Motors are literally '
      'everywhere, everything from linear motion to water-pumps and turbines often start as '
      'rotation driven by motors, and without them the world would be a much more stationary '
      'place (you could almost say motors make the world turn&hellip;).'),
    lead('I wanted to know how motors work, so I built one entirely from scratch. Everything from '
         'the stator windings to the magnetic rotor, I specced, designed, built, and tested. '
         'Moreover, to make it more challenging and to squeeze a little bit more efficiency out of '
         'it, I designed the motor specifically for Field Oriented Control meaning the need for a '
         'magnetic encoder, distributed windings, and large arc magnets.'),
    p('Being a personal project, much of this build was constrained by budgets, but through various '
      'attempts to compromise and de-scope, I was able to assemble a first prototype which is '
      'currently being tested. The ultimate goal of this project is to use the motor in a larger '
      'DIY OneWheel build which has been a dream of mine for a while.'),

    h('Design'),
    p('I began by defining my constraints then modeled everything in SolidWorks, since this first '
      'prototype would be largely 3D printed, everything was designed with a heavy focus on DFM '
      'for FDM printing.'),
    pair(img('p1-cad-section', 'Section view of the hub motor assembly in SolidWorks'),
         img('p1-cad-exploded', 'Exploded view of the hub motor assembly')),
    img('p1-stator-housing', 'The wound stator seated in its printed housing'),
    img('p1-winding',
        'Winding diagram for the 36-slot stator: three phases distributed across the slots, '
        'with the rotor magnet arcs shown on the outer ring',
        'The winding layout I worked out for the 36-slot stator &mdash; three phases distributed '
        'across the slots, with the rotor&rsquo;s magnet arcs on the outer ring.',
        narrow=True),

    h('Field Oriented Control'),
    p('I wanted to use field oriented control (FOC) to drive this motor. This meant two things that '
      'needed to be different from a typical motor: encoder to detect position, and large arc '
      'magnets in the rotor.'),
    p('Finding a place to put a magnetic encoder proved difficult because it meant needing to split '
      'the shaft to make the encoder concentric with the motor, however, supporting the stator from '
      'only one end would severely compromise its rigidity which is a concern as it experiences '
      'extreme magnetic forces.'),
    p('I designed a way to place the encoder inside the shaft by splitting the shaft and decoupling '
      'it from the rotor using bearings.'),
    pair(img('p1-encoder-original', 'Original encoder layout, stator supported from one end only',
             'Original design &mdash; making the encoder concentric meant supporting the stator from a single end.'),
         img('p1-encoder-new', 'Revised layout with a split shaft and the encoder carried inside it',
             'New design &mdash; the shaft is split and decoupled from the rotor by bearings, with the encoder living inside.')),

    p('Wide angle arc magnets are vital for creating a sinusoidal back-EMF profile. However, large '
      'arc magnets are hard to find in the proper dimensions, which makes custom ordering the only '
      'option, but this obviously greatly exceeds my budget for this project.'),
    p('To compromise, I approximated arc magnets using smaller block magnets placed adjacently. '
      'Block magnets are much cheaper.'),
    p('I validated that this works by using magnetic sensitive sheets to visualize the magnetic '
      'fields, and indeed the magnetic field appeared uniform in the regions they should be.'),
    pair(img('p1-rotor', 'Rotor with block magnets arranged to approximate wide arc magnets'),
         img('p1-magfield', 'Magnetic viewing film held against the rotor to check field uniformity')),

    h('Back-EMF Validation'),
    p('Using an oscilloscope I could verify that the back-EMF from spinning the motor was roughly '
      'sinusoidal. The 6 spikes seen can be attributed to the 6 individual magnets in each arc '
      'cogging with the stator.'),
    row(video('backemf-validation', 'poster-backemf-validation',
              'Back-EMF measured on an oscilloscope while the motor is spun by hand'),
        img('p1-scope',
            'Oscilloscope trace showing a roughly sinusoidal back-EMF with six cogging spikes')),
  ],
},
{
  'slug':  'forc-speed-controller',
  'brief': "FORC is a high-power ESC for field oriented control, laid out in Altium around the Vedder architecture. It was my first PCB, taken from no experience at all to a finished board.",
  'title': 'FORC Speed Controller',
  'blurb': 'A high-power ESC built around the Vedder architecture &mdash; and a first '
           'attempt at PCB design, in Altium.',
  'cover': 'cover-forc',
  'tile':  't-forc',
  'body': [
    img('p2-cover', '3D render of the FORC speed controller PCB'),
    h('Objective'),
    p('Before starting this project, I had no experience in PCB design, at all. I had never touched '
      'a PCB software nor taken any advanced circuits courses. However, knowing how universal the '
      'applications of printed circuit boards are, I wanted to learn the process of how they are '
      'designed.'),
    lead('So, I designed FORC, my attempt at a high-power ESC specifically designed for Field '
         'Oriented Control. The software I used was Altium, which I chose over other beginner '
         'friendly choices like KiCad because it is more of an industry standard. My design is '
         'based on the Vedder ESC architecture, which is the gold standard for speed controllers '
         'in the application I am looking for.'),
    p('The ultimate goal of FORC is to use it to drive my DIY OneWheel build, which is why it '
      'required specific components like an IMU and FSR sensor.'),
    img('p2-top', 'Top-down render of the FORC board showing the power stage and connectors'),
    img('p2-layout', 'Altium board layout of FORC with copper pours and routing visible'),
  ],
},
{
  'slug':  'pool-robot',
  'brief': "An omni-directional VEX robot that locates a pool ball using a single laser distance sensor and strikes it into a pocket. I designed the scissor striking mechanism and wrote the ball detection algorithm in C++.",
  'title': 'Autonomous Pool-Playing Robot',
  'blurb': 'An omni-directional VEX robot that finds a pool ball with one laser sensor '
           'and strikes it into a pocket.',
  'cover': 'cover-pool',
  'tile':  't-pool',
  'body': [
    pair(img('p3-cover', 'The autonomous pool-playing robot on the table'),
         img('p3-team', 'The project team with the robot at the pool table')),
    h('Objective'),
    p('The Autonomous Pool-Playing Robot was built as a group project for my final Mechatronics '
      'Project of first year. The robot was built around standard VEX components, and our goal was '
      'to push these components to the limits of their capabilities.'),
    lead('My group and I designed, coded and tested an omni-directional robot which could '
         'successfully locate and strike a pool ball into a pocket.'),
    p('My contribution to this project was in the mechanical design of the striking mechanism and '
      'the ball detection algorithm I wrote in C++.'),

    h('Ball Detection Algorithm'),
    p('The ball detection algorithm was constrained by a single laser distance sensor which forced '
      'out-of-the-box thinking to be able to locate the ball. To achieve both efficiency and '
      'accuracy, I split the algorithm into two parts:'),
    steps(
      {'no': 'Step 1:',
       'text': 'The robot does a rotating pass across the whole table. By using the robots current '
               'position and the dimensions of the table, the theoretical wall distance could be '
               'calculated and compared to the laser sensor data. Any large discrepancies between '
               'the theoretical and measured distance was flagged as a ball.',
       'media': video('pool-general-scan', 'poster-pool-general-scan',
                      'The robot performing a rotating scan of the whole table')},
      {'no': 'Step 2:',
       'text': 'After finding the rough direction of the ball, the robot does a slower scan to '
               'detect the outer edges of the ball, from these two edges, the robot can align '
               'itself with the exact center of the ball.',
       'media': video('pool-ball-centering', 'poster-pool-ball-centering',
                      'The robot scanning slowly to find both edges of the ball and centre on it')}),

    h('Striking Mechanism'),
    p('After many revisions, the final design I settled on used a scissor mechanism to ensure the '
      'front face stayed perpendicular with the forward direction.'),
    pair(img('p3-strike-detail', 'Close-up of the scissor linkage driving the striking face'),
         img('p3-strike-full', 'The complete robot showing the striking face extended')),

    h('Full Video Demo'),
    video('pool-full-demo', 'poster-pool-full-demo',
          'Full demonstration of the robot locating and striking the ball into a pocket',
          replay=True, speed=True),
  ],
},
{
  'slug':  'autocleat',
  'brief': "A shoe attachment that deploys ice spikes when winter surfaces turn unsafe and retracts them indoors, so you never stop to change footwear. Built in 24 hours at Waterloo EngHacks.",
  'title': 'AutoCleat',
  'blurb': 'A shoe attachment that deploys ice spikes only when it needs to &mdash; '
           'built in 24 hours at Waterloo EngHacks.',
  'cover': 'cover-cleat',
  'tile':  't-cleat',
  'body': [
    img('p4-cover', 'AutoCleat mounted on a shoe with its control electronics'),
    h('Objective'),
    p('AutoCleat is a shoe attachment that automatically deploys ice spikes when winter surfaces '
      'become unsafe. It was designed to solve the awkwardness of traditional cleats, which work '
      'outdoors but become inconvenient or damaging when walking indoors.'),
    p('AutoCleat was built in 24 hours as a submission to the Waterloo Enghacks Hackathon.'),
    row(img('p4-shoe-side', 'Side view of the AutoCleat frame strapped to a shoe'),
        img('p4-shoe-worn', 'AutoCleat being worn, with wiring to the ankle-mounted controller')),
    img('p4-prototype', 'The AutoCleat prototype and its ankle cuff on the bench'),
    p('The prototype uses temperature sensing to detect icy conditions and an ultrasonic foot-lift '
      'sensor to deploy TPU spikes only when the foot is raised. The spikes retract on safe '
      'surfaces, giving the user hands-free traction control without stopping, bending down, or '
      'manually switching modes.'),
    video('autocleat-demo', 'poster-autocleat-demo',
          'AutoCleat deploying and retracting its spikes on demand', replay=True),
  ],
},
{
  'slug':  'cycloidal-gearbox',
  'brief': "A compact cycloidal reducer for robotic joints &mdash; a high reduction ratio packed into a package just 22&nbsp;mm thick.",
  'title': 'Cycloidal Gearbox for Robotic Joints',
  'blurb': 'A compact 22&nbsp;mm-thick cycloidal reducer designed for robotic joints.',
  'cover': 'cover-cycloid',
  'tile':  't-cycloid',
  'body': [
    img('p5-photo-a', 'The printed cycloidal gearbox with its output arm attached'),
    h('Objective'),
    p('This cycloidal gearbox was designed to be a compact reducer for use in robotic joints. '
      'The final dimensions measure 22mm in thickness.'),
    row(img('p5-photo-b', 'Top view of the assembled cycloidal gearbox showing its low profile'),
        img('p5-exploded', 'Exploded CAD view of the cycloidal gearbox internals')),
  ],
},
{
  'slug':  'rocket-trailer',
  'brief': "An accurate SolidWorks model of the team&rsquo;s transport trailer, which became the reference every rocket transport fixture was designed against. The full assembly is explorable in 3D inside.",
  'title': 'Rocket Transport Trailer CAD',
  'blurb': 'An accurate SolidWorks model of the team&rsquo;s transport trailer &mdash; the '
           'reference every launch fixture was designed against.',
  'cover': 'cover-trailer',
  'tile':  't-trailer',
  'body': [
    img('p6-cover', 'CAD render of the rocket transport trailer deck and rails'),
    h('Objective'),
    p('I created an accurate model of a transport trailer in CAD (SolidWorks) which proved to be '
      'mission critical for designing fixtures to transport the Team&rsquo;s rocket to the launch '
      'site.'),
    img('p6-cad-iso', 'Isometric CAD view of the complete trailer model'),
    stack(img('p6-real', 'Photograph of the real transport trailer'),
          img('p6-cad-side', 'Side elevation of the CAD trailer model for comparison')),
    h('Explore the model'),
    cad('assets/model/trailer.glb'),
  ],
},
]

# --------------------------------------------------------------------------- #
#  renderers
# --------------------------------------------------------------------------- #
def r_img(b, base, cls=''):
    cap = ('\n      <figcaption>%s</figcaption>' % b['cap']) if b.get('cap') else ''
    cls = (cls + ' figure--narrow').strip() if b.get('narrow') else cls
    return ('    <figure class="%s">\n'
            '      <img src="%sassets/img/%s.webp" alt="%s"%s loading="lazy" decoding="async">%s\n'
            '    </figure>' % (cls, base, b['src'], html.escape(b['alt'], quote=True),
                               dims(b['src']), cap))

def r_video(b, base, cls=''):
    cap = ('\n      <figcaption>%s</figcaption>' % b['cap']) if b.get('cap') else ''
    vid = ('<video data-autoplay muted loop playsinline preload="none"%s\n'
           '               poster="%sassets/img/%s.webp" aria-label="%s">\n'
           '          <source src="%sassets/video/%s.mp4" type="video/mp4">\n'
           '          <source src="%sassets/video/%s.webm" type="video/webm">\n'
           '        </video>' % (dims(b['poster']), base, b['poster'],
                                 html.escape(b['alt'], quote=True),
                                 base, b['src'], base, b['src']))
    tools = ''
    if b.get('replay'):
        tools += ('          <button type="button" class="video-btn video-replay" data-replay>\n'
                  '            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" aria-hidden="true">\n'
                  '              <path d="M1 4v6h6M3.5 15a9 9 0 1 0 2.1-9.4L1 10" stroke="currentColor"\n'
                  '                    stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>\n'
                  '            </svg>Replay\n'
                  '          </button>\n')
    if b.get('speed'):
        tools += ('          <button type="button" class="video-btn video-speed" data-speed\n'
                  '                  aria-label="Playback speed">1&times;</button>\n')
    if tools:
        body = ('      <div class="video-wrap">\n'
                '        %s\n'
                '        <div class="video-tools">\n'
                '%s'
                '        </div>\n'
                '      </div>' % (vid, tools))
    else:
        body = '      %s' % vid
    return '    <figure class="%s">\n%s%s\n    </figure>' % (cls, body, cap)

def r_block(b, base):
    k = b['k']
    if k == 'h':    return '    <h3 class="section-title">%s</h3>' % b['text']
    if k == 'p':    return '    <p>%s</p>' % b['text']
    if k == 'lead': return '    <p class="lead">%s</p>' % b['text']
    if k == 'img':  return r_img(b, base)
    if k == 'video':return r_video(b, base)
    if k == 'pair':
        inner = '\n'.join(r_img(i, base) if i['k'] == 'img' else r_video(i, base) for i in b['items'])
        return '    <div class="media-pair">\n%s\n    </div>' % inner
    if k == 'row':
        cells = []
        for it in b['items']:
            ar = aspect(it['src'] if it['k'] == 'img' else it['poster'])
            inner = r_img(it, base) if it['k'] == 'img' else r_video(it, base)
            cells.append('      <div class="media-row__cell" style="flex:%.4f 1 0">\n%s\n'
                         '      </div>' % (ar, inner))
        return '    <div class="media-row">\n%s\n    </div>' % '\n'.join(cells)
    if k == 'stack':
        inner = '\n'.join(r_img(i, base) if i['k'] == 'img' else r_video(i, base) for i in b['items'])
        return '    <div class="media-stack">\n%s\n    </div>' % inner
    if k == 'steps':
        cols = []
        for s in b['items']:
            media = r_video(s['media'], base) if s['media']['k'] == 'video' else r_img(s['media'], base)
            cols.append('      <div class="step">\n'
                        '        <p class="step__no">%s</p>\n'
                        '        <p>%s</p>\n%s\n      </div>' % (s['no'], s['text'], media))
        return '    <div class="steps">\n%s\n    </div>' % '\n'.join(cols)
    if k == 'cad':
        cap = ('\n      <figcaption>%s</figcaption>' % b['cap']) if b.get('cap') else ''
        return ('    <figure>\n'
                '      <div class="cad" data-model="%s%s">\n'
                '        <canvas class="cad__stage"></canvas>\n'
                '        <div class="cad__status">Loading model&hellip;</div>\n'
                '        <div class="cad__hint">Drag to orbit &middot; scroll to zoom</div>\n'
                '        <button type="button" class="cad__reset">Reset view</button>\n'
                '      </div>%s\n'
                '    </figure>' % (base, b['model'], cap))
    return ''

def project_body(pr, base, uid=''):
    """Leading media stays visible; from the first sub-heading on, the content
    lives behind the 'dive deeper' toggle."""
    body = pr['body']
    cut = next((i for i, b in enumerate(body) if b['k'] == 'h'), len(body))
    lead_html = '\n'.join(r_block(b, base) for b in body[:cut])
    deep_html = '\n'.join(r_block(b, base) for b in body[cut:])
    did = 'deep-%s%s' % (pr['slug'], uid)
    out = []
    if lead_html:
        out.append(lead_html)
    out.append("""    <div class="brief">
      <div class="brief__head">
        <h3 class="section-title">In Brief</h3>
        <button type="button" class="dive" data-dive aria-expanded="false" aria-controls="%s">
          <span class="dive__label">dive deeper</span>
          <svg width="11" height="11" viewBox="0 0 12 12" fill="none" aria-hidden="true">
            <path d="M1.6 4 6 8.4 10.4 4" stroke="currentColor" stroke-width="1.6"
                  stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
      <p class="lead">%s</p>
    </div>
    <div class="deep" id="%s">
      <div class="deep__inner">
%s
      </div>
    </div>""" % (did, pr['brief'], did, deep_html))
    return '\n'.join(out)

# --------------------------------------------------------------------------- #
#  chrome
# --------------------------------------------------------------------------- #
def header(base, home, current=None):
    def cur(x): return ' aria-current="page"' if current == x else ''
    return f'''<header class="site-header">
  <div class="wrap site-header__inner">
    <a class="brand" href="{home}" aria-label="Austin Li — back to the top">
      <div class="brand__name">Austin&nbsp;Li</div>
      <div class="brand__role">Mechatronics Engineer</div>
    </a>
    <nav class="nav" aria-label="Primary">
      <a href="{base}gallery.html"{cur('gallery')}>projects gallery</a>
      <a href="{base}{SITE['resume']}" target="_blank" rel="noopener">resume</a>
      <a href="{SITE['linkedin']}" target="_blank" rel="noopener">LinkedIn</a>
      <a href="{SITE['github']}" target="_blank" rel="noopener">Github</a>
      <button type="button" data-contact-open>Contact me</button>
    </nav>
  </div>
</header>'''

def modal():
    return f'''<div class="modal" id="contact-modal" role="dialog" aria-modal="true"
     aria-labelledby="contact-title" aria-hidden="true">
  <div class="modal__scrim" data-contact-close></div>
  <div class="modal__panel">
    <button type="button" class="modal__close" data-contact-close aria-label="Close">&#10005;</button>
    <h2 class="modal__title" id="contact-title">Contact me</h2>
    <div class="modal__rows">
      <div class="modal__row">
        <span class="modal__key">Email</span>
        <a class="modal__val" href="mailto:{SITE['email']}">{SITE['email']}</a>
      </div>
      <div class="modal__row">
        <span class="modal__key">Phone</span>
        <a class="modal__val" href="tel:{SITE['phone_href']}">{SITE['phone']}</a>
      </div>
    </div>
    <p class="modal__note">{SITE['note']}</p>
  </div>
</div>'''

def footer(base):
    return f'''<footer class="site-footer">
  <div class="wrap site-footer__inner">
    <span>&copy; 2026 Austin Li</span>
    <nav aria-label="Elsewhere">
      <a href="{base}gallery.html">Projects gallery</a>
      <a href="{base}{SITE['resume']}" target="_blank" rel="noopener">Resume</a>
      <a href="{SITE['linkedin']}" target="_blank" rel="noopener">LinkedIn</a>
      <a href="{SITE['github']}" target="_blank" rel="noopener">Github</a>
      <a href="mailto:{SITE['email']}">Email</a>
    </nav>
  </div>
</footer>'''

FAVICON = ('data:image/svg+xml,'
           "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
           "%3Crect width='32' height='32' rx='7' fill='%23303030'/%3E"
           "%3Ctext x='16' y='22' font-family='Helvetica,Arial,sans-serif' font-size='15' "
           "font-weight='600' fill='%23f1eeeb' text-anchor='middle'%3EAL%3C/text%3E%3C/svg%3E")

def shell(title, desc, base, body, og_img, scripts=('site',), current=None, cls=''):
    js = '\n'.join('<script src="%sassets/js/%s.js" defer></script>' % (base, s) for s in scripts)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>document.documentElement.className += ' js';</script>
<title>{title}</title>
<meta name="description" content="{html.escape(desc, quote=True)}">
<meta name="author" content="Austin Li">
<meta name="theme-color" content="#f1eeeb">
<link rel="icon" href="{FAVICON}">
<meta property="og:type" content="website">
<meta property="og:title" content="{html.escape(title, quote=True)}">
<meta property="og:description" content="{html.escape(desc, quote=True)}">
<meta property="og:image" content="{SITE['url']}/assets/img/{og_img}.webp">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700&amp;family=Inter:wght@300;400;500;600&amp;display=swap">
<link rel="stylesheet" href="{base}assets/css/site.css">
{js}
</head>
<body{(' class="%s"' % cls) if cls else ''}>
<a class="skip-link" href="#main">Skip to content</a>
{body}
{modal()}
</body>
</html>
'''

# --------------------------------------------------------------------------- #
#  pages
# --------------------------------------------------------------------------- #
def build_index():
    base, home = '', '#top'
    projects_html = []
    for i, pr in enumerate(PROJECTS):
        projects_html.append(f'''  <article class="project" data-project data-project-no="{i+1:02d}" id="{pr['slug']}">
    <div class="col project__head">
      <p class="project__eyebrow">Project {i+1:02d}</p>
      <h2 class="project__title">{pr['title']}</h2>
    </div>
    <div class="col">
{project_body(pr, base, '-main')}
    </div>
  </article>''')

    body = f'''{header(base, home)}
<main id="main">
  <span id="top"></span>

  <section class="hero wrap">
    <div class="hero__grid reveal">
      <img class="hero__photo" src="assets/img/headshot.webp"
           alt="Portrait of Austin Li" width="1100" height="1375" fetchpriority="high">
      <div>
        <h1 class="hero__title">Hi, I&rsquo;m Austin Li</h1>
        <p class="hero__lede">{SITE['lede']}</p>
      </div>
    </div>
  </section>

  <section class="projects" data-rail-section aria-labelledby="projects-heading">
    <div class="rail" aria-hidden="true">
      <div class="rail__track"></div>
      <div class="rail__fill"></div>
    </div>

    <div class="col projects__head reveal">
      <h2 id="projects-heading">PROJECTS</h2>
    </div>

{chr(10).join(projects_html)}
  </section>
</main>

<button type="button" class="skip-next" aria-label="Skip to the next project">
  <span>skip to the next project</span>
  <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
    <path d="M6.5 1v10M2.5 7.2l4 4 4-4" stroke="currentColor" stroke-width="1.4"
          stroke-linecap="round" stroke-linejoin="round"/>
  </svg>
</button>

{footer(base)}'''

    return shell('Austin Li — Mechatronics Engineer',
                 'Portfolio of Austin Li, a Waterloo Mechatronics Engineering student: motors, '
                 'motor control, robotics and mechanical design.',
                 base, body, 'cover-motor', scripts=('site', 'cadview'))

def build_gallery():
    base = ''
    tiles = []
    for pr in PROJECTS:
        tiles.append(f'''      <a class="tile {pr['tile']}" href="projects/{pr['slug']}.html">
        <img src="assets/img/{pr['cover']}.webp" alt="{html.escape(pr['title'], quote=True)}"{dims(pr['cover'])}
             loading="lazy" decoding="async">
        <span class="tile__label"><span>{pr['title']}</span></span>
      </a>''')

    body = f'''{header(base, 'index.html#top', current='gallery')}
<main id="main">
  <section class="wrap gallery-head reveal">
    <h1>PROJECTS</h1>
    <p>Six things I designed, built and tested. Each one opens on its own page.</p>
  </section>
  <section class="wrap">
    <div class="bento">
{chr(10).join(tiles)}
    </div>
  </section>
</main>
{footer(base)}'''

    return shell('Projects — Austin Li',
                 'A gallery of Austin Li&rsquo;s mechatronics projects: hub motors, motor '
                 'controllers, robotics and CAD.',
                 base, body, 'cover-motor')

def build_project(i, pr):
    base = '../'
    prev = PROJECTS[i-1] if i > 0 else None
    nxt  = PROJECTS[i+1] if i < len(PROJECTS)-1 else None

    left = (f'''<a href="{prev['slug']}.html"><span class="pager__label">Previous</span>{prev['title']}</a>'''
            if prev else '<span></span>')
    right = (f'''<a href="{nxt['slug']}.html" style="text-align:right"><span class="pager__label">Next</span>{nxt['title']}</a>'''
             if nxt else '<span></span>')

    body = f'''{header(base, base + 'index.html#top')}
<main id="main" class="page-project">
  <section class="projects" data-rail-section>
    <div class="rail" aria-hidden="true">
      <div class="rail__track"></div>
      <div class="rail__fill"></div>
    </div>
    <article class="project" data-project data-project-no="{i+1:02d}" id="{pr['slug']}">
      <div class="col project__head">
        <p class="crumbs"><a href="{base}index.html">Austin Li</a> &nbsp;/&nbsp;
          <a href="{base}gallery.html">Projects</a></p>
        <p class="project__eyebrow">Project {i+1:02d}</p>
        <h2 class="project__title">{pr['title']}</h2>
      </div>
      <div class="col">
{project_body(pr, base)}
      </div>
    </article>
  </section>

  <div class="col">
    <nav class="pager" aria-label="Other projects">
      {left}
      {right}
    </nav>
  </div>
</main>
{footer(base)}'''

    desc = pr['blurb'].replace('&mdash;', '—').replace('&rsquo;', '’').replace('&nbsp;', ' ')
    return shell(f"{pr['title']} — Austin Li", desc, base, body, pr['cover'],
                 scripts=('site', 'cadview'), cls='')

# --------------------------------------------------------------------------- #
def write(path, text):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w') as f:
        f.write(text)
    print('%-42s %6.1f KB' % (path, len(text)/1024))

def main():
    write('index.html',   build_index())
    write('gallery.html', build_gallery())
    for i, pr in enumerate(PROJECTS):
        write('projects/%s.html' % pr['slug'], build_project(i, pr))
    open(os.path.join(OUT, '.nojekyll'), 'w').close()

if __name__ == '__main__':
    main()
