import zipfile, xml.etree.ElementTree as ET, math, os, re, json
from pathlib import Path

BASE = Path(r'C:\Users\HP\Downloads\Tiktok Visual.pptx')
OUT = Path.cwd() / 'Facebook_Sentiment_System_Presentation.pptx'
EMU = 914400
W, H = 13.333333, 7.5
# Design cues sampled from the supplied reference deck.
BG = '09051B'; PANEL = '15102D'; PANEL2 = '20183E'; STROKE = '302554'
CYAN = '28DDF5'; PINK = 'FF4FD8'; PURPLE = '9B6BFF'; MINT = '32E6C5'
WHITE = 'EAF3FF'; MUTED = 'A7B4D0'; PALE = 'E6EEE5'; FONT = 'Aptos'
NS_A='http://schemas.openxmlformats.org/drawingml/2006/main'
NS_P='http://schemas.openxmlformats.org/presentationml/2006/main'
NS_R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
ET.register_namespace('a',NS_A); ET.register_namespace('p',NS_P); ET.register_namespace('r',NS_R)
A=lambda n:'{%s}%s'%(NS_A,n); P=lambda n:'{%s}%s'%(NS_P,n); R=lambda n:'{%s}%s'%(NS_R,n)

def E(tag, attrs=None, children=()):
    x=ET.Element(tag, attrs or {})
    for c in children: x.append(c)
    return x

def emu(v): return str(round(v*EMU))

def tx_run(p, s, size, color, bold=False, italic=False):
    r=E(A('r')); rp=E(A('rPr'),{'lang':'en-US','sz':str(round(size*100)),'b':'1' if bold else '0','i':'1' if italic else '0'})
    rp.append(E(A('solidFill'),children=[E(A('srgbClr'),{'val':color})])); rp.append(E(A('latin'),{'typeface':FONT})); r.append(rp)
    t=E(A('t')); t.text=s; r.append(t); p.append(r)

def add_shape(tree, sid, x,y,w,h, text=None, size=14, color=WHITE, bold=False, fill=None, line=None, radius=True, align='l', valign='ctr', margin=.12, italic=False, geom=None):
    sp=E(P('sp')); nv=E(P('nvSpPr')); nv.append(E(P('cNvPr'),{'id':str(sid),'name':f'Shape {sid}'})); nv.append(E(P('cNvSpPr'))); nv.append(E(P('nvPr'))); sp.append(nv)
    sppr=E(P('spPr')); sppr.append(E(A('xfrm'),children=[E(A('off'),{'x':emu(x),'y':emu(y)}),E(A('ext'),{'cx':emu(w),'cy':emu(h)})]))
    prst=geom or ('roundRect' if radius else 'rect'); geomel=E(A('prstGeom'),{'prst':prst}); geomel.append(E(A('avLst'))); sppr.append(geomel)
    if fill: sppr.append(E(A('solidFill'),children=[E(A('srgbClr'),{'val':fill})]))
    else: sppr.append(E(A('noFill')))
    if line: sppr.append(E(A('ln'),{'w':'12700'},[E(A('solidFill'),children=[E(A('srgbClr'),{'val':line})])]))
    else: sppr.append(E(A('ln'),children=[E(A('noFill'))]))
    sp.append(sppr)
    body=E(P('txBody')); body.append(E(A('bodyPr'),{'wrap':'square','anchor':valign,'lIns':emu(margin),'rIns':emu(margin),'tIns':emu(margin/2),'bIns':emu(margin/2)})); body.append(E(A('lstStyle')))
    if text is None: text=''
    for line_text in str(text).split('\n'):
        p=E(A('p')); pp=E(A('pPr'),{'algn':{'l':'l','ctr':'ctr','r':'r'}.get(align,'l'),'marL':'0','indent':'0'}); pp.append(E(A('buNone'))); p.append(pp)
        if line_text: tx_run(p,line_text,size,color,bold,italic)
        p.append(E(A('endParaRPr'),{'lang':'en-US','sz':str(round(size*100))})); body.append(p)
    sp.append(body); tree.append(sp); return sid+1

class Slide:
    def __init__(self, num, section, title, footer=True):
        self.root=E(P('sld'),{'showMasterSp':'0'}); self.cSld=E(P('cSld')); self.root.append(self.cSld)
        bg=E(P('bg')); bgpr=E(P('bgPr')); bgpr.append(E(A('solidFill'),children=[E(A('srgbClr'),{'val':BG})])); bgpr.append(E(A('effectLst'))); bg.append(bgpr); self.cSld.append(bg)
        tree=E(P('spTree')); self.cSld.append(tree); tree.append(E(P('nvGrpSpPr'),children=[E(P('cNvPr'),{'id':'1','name':''}),E(P('cNvGrpSpPr')),E(P('nvPr'))])); tree.append(E(P('grpSpPr'),children=[E(A('xfrm'),children=[E(A('off'),{'x':'0','y':'0'}),E(A('ext'),{'cx':'0','cy':'0'}),E(A('chOff'),{'x':'0','y':'0'}),E(A('chExt'),{'cx':'0','cy':'0'})])]))
        self.t=tree; self.sid=2
        if section:
            self.text(.64,.26,section,10,CYAN,True,w=11.9,h=.26)
            self.text(.64,.63,title,26,WHITE,True,w=12.1,h=.56)
        if footer:
            self.text(.64,7.16,'FACEBOOK SENTIMENT SYSTEM  ·  DATA SCIENCE',7.3,MUTED,True,w=9.8,h=.18)
            self.text(12.05,7.13,f'{num:02d}',8,CYAN,True,w=.62,h=.2,align='r')
    def text(self,x,y,s,size=14,color=WHITE,bold=False,w=4,h=.35,align='l',valign='ctr',margin=.02,italic=False):
        self.sid=add_shape(self.t,self.sid,x,y,w,h,s,size,color,bold,align=align,valign=valign,margin=margin,italic=italic,radius=False)
    def box(self,x,y,w,h,fill=PANEL,line=STROKE,radius=True):
        self.sid=add_shape(self.t,self.sid,x,y,w,h,None,fill=fill,line=line,radius=radius)
    def card(self,x,y,w,h,title,body=None,accent=CYAN, num=None, body_size=12):
        self.box(x,y,w,h,PANEL,STROKE)
        self.box(x+.02,y+.12,.045,h-.24,accent,accent,False)
        if num is not None: self.text(x+.20,y+.15,num,12,accent,True,w=.46,h=.3)
        self.text(x+(.72 if num is not None else .20),y+.14,title,15,WHITE,True,w=w-(.95 if num is not None else .4),h=.38)
        if body: self.text(x+.20,y+.62,body,body_size,MUTED,False,w=w-.4,h=h-.74,valign='t',margin=.01)
    def xml(self):
        self.cSld.append(E(P('clrMapOvr'),children=[E(A('masterClrMapping'))]))
        return ET.tostring(self.root,encoding='utf-8',xml_declaration=True)

slides=[]
# 01 Cover
s=Slide(1,None,None,False)
s.box(8.52,.34,4.42,6.78,PANEL,STROKE)
s.box(8.82,.68,3.82,.065,CYAN,CYAN,False)
s.text(.75,.56,'PROJETU ANALÍTIKA NO SENTIMENTU DADUS FACEBOOK',10,CYAN,True,w=7.4,h=.34)
s.text(.75,1.42,'SISTEMA ANALÍTIKU\nBA KOMENTÁRIU\nFACEBOOK',31,WHITE,True,w=7.35,h=1.78,valign='t',margin=0)
s.text(.78,3.43,'Sistema Analítiku ba Komentáriu Facebook',16,MUTED,True,w=7.15,h=.42)
s.text(.78,4.02,'Analiza sentimentu, preprocessing, labeling, Machine Learning no dashboard interativu.',12,MUTED,False,w=6.9,h=.76,valign='t',margin=0)
s.text(.78,5.23,'Apresenta: [NARAN]',11,WHITE,True,w=4.6,h=.3)
s.text(.78,5.65,'DATA SCIENCE',9,CYAN,True,w=3.0,h=.28)
s.text(.78,6.54,'DADUS  →  INSIGHT',12,WHITE,True,w=4.6,h=.35)
s.text(9.05,1.02,'SENTIMENTU',9,MUTED,True,w=2.7,h=.25)
for i,(label,col,sub) in enumerate([('Positive',MINT,'SINAL POSITIVU'),('Neutral',CYAN,'SINAL NEUTRU'),('Negative',PINK,'SINAL NEGATIVU')]):
    y=1.52+i*1.22; s.box(9.02,y,3.3,.82,PANEL2,STROKE); s.box(9.02,y,.07,.82,col,col,False); s.text(9.27,y+.12,label,17,WHITE,True,w=2.7,h=.31); s.text(9.28,y+.48,sub,8,col,True,w=2.7,h=.2)
s.box(9.02,5.46,3.3,.92,'202554','202554'); s.text(9.24,5.61,'DASHBOARD',10,CYAN,True,w=2.8,h=.25); s.text(9.24,5.94,'INTERATIVU  ·  FACEBOOK',9,WHITE,True,w=2.8,h=.23)
s.text(.75,7.16,'FACEBOOK SENTIMENT SYSTEM  ·  DATA SCIENCE',7.3,MUTED,True,w=9.8,h=.18); s.text(12.05,7.13,'01',8,CYAN,True,w=.62,h=.2,align='r'); slides.append(s)
# 02 Context
s=Slide(2,'01 · KONTEKSTU','Kontekstu: komentáriu Facebook barak, informasaun barak')
s.card(.72,1.7,3.86,2.45,'Komentáriu mak sinal','Komentáriu hatudu opiniaun, pergunta no reasaun utilizadór liuhosi testu, likes no comments.',CYAN,body_size=12)
s.card(4.74,1.7,3.86,2.45,'Dadus difisil atu haree','Bainhira komentáriu barak, leitura manual susar atu kompara sentimentu, tempu no engagement.',PINK,body_size=12)
s.card(8.76,1.7,3.86,2.45,'Visual ajuda komprende','Dashboard transforma tabela ba gráfiku, filtrajen no insight ne’ebé fasil atu lee.',MINT,body_size=12)
s.box(.72,4.55,11.9,1.55,'20183E',STROKE); s.text(1.0,4.77,'KONTEKSTU DADUS ATUAL',9,CYAN,True,w=4.0,h=.24); s.text(1.0,5.12,'1,679',28,WHITE,True,w=2.2,h=.5); s.text(3.0,5.18,'Facebook records iha database',12,MUTED,False,w=4.8,h=.34); s.text(8.4,5.2,'Komentáriu  →  sentimentu  →  insight',11,WHITE,True,w=3.8,h=.3,align='r'); slides.append(s)
# 03 Problem
s=Slide(3,'02 · PROBLEMA','Problema ne’ebé sistema hakarak responde')
problems=[('01','Dadus raw presiza limpeza.','URL, mention, emoji no HTML bele aumenta noise.',CYAN),('02','Label presiza jestaun.','Sentimentu tenke fahe ba Positive, Neutral no Negative.',PINK),('03','Leitura manual la eficiente.','Komentáriu barak difisil atu kompara ho lalais.',MINT),('04','Predisaun presiza model.','Dadus label uza atu treina Decision Tree.',PURPLE),('05','Dadus presiza vizualizasaun.','Dashboard ajuda haree distribuisaun no padraun.',CYAN),('06','Kualidade presiza verifikasaun.','Evaluation presiza test set ho klase sufisiente.',PINK)]
for i,(n,t,b,c) in enumerate(problems):
 x=.72+(i%3)*4.02; y=1.65+(i//3)*2.15; s.card(x,y,3.82,1.8,t,b,c,n,11)
s.box(.72,6.12,11.9,.54,'20183E',STROKE); s.text(.98,6.22,'REZULTADU HAKARAK: insight ne’ebé klaru husi komentáriu barak.',11,CYAN,True,w=11.3,h=.3); slides.append(s)
# 04 Objectives
s=Slide(4,'03 · OBJETIVU','Objetivu projetu')
obj=[('01','Analiza','Klasifika sentimentu: Positive, Neutral no Negative.',CYAN),('02','Preprocess','Limpa emoji, URL, mention, HTML no whitespace.',PINK),('03','Label','Atribui label sentimentu ba komentáriu.',MINT),('04','Train','Treina no avalia model Decision Tree.',PURPLE),('05','Visualiza','Hatudu rezultadu iha dashboard interativu.',CYAN),('06','Jere dadus','Import dataset, jere wordlist no utilizadór.',PINK)]
for i,(n,t,b,c) in enumerate(obj):
 x=.72+(i%3)*4.02; y=1.58+(i//3)*2.03; s.card(x,y,3.82,1.7,t,b,c,n,11)
s.box(.72,5.85,11.9,.7,'20183E',STROKE); s.text(1.02,6.03,'OBJETIVU',9,CYAN,True,w=1.15,h=.22); s.text(2.35,6.0,'Dadus  →  model  →  insight ne’ebé klaru',15,WHITE,True,w=9.6,h=.32); slides.append(s)
# 05 Data
s=Slide(5,'04 · DADUS','Dadus no variável importante')
for x,n,label,c in [(.72,'1,679','Total records',CYAN),(3.77,'1,469','Clean records¹',MINT),(6.82,'138','Duplicate records',PINK),(9.87,'72','Missing text',PURPLE)]:
 s.box(x,1.55,2.72,1.18,PANEL,STROKE); s.text(x+.18,1.7,n,26,c,True,w=2.35,h=.48); s.text(x+.2,2.24,label,10,MUTED,True,w=2.3,h=.24)
for x,y,w,h,t,b,c in [(.72,3.05,5.78,1.18,'KOLUNA KONTENTU','text  ·  cleaned_text  ·  language\nsentiment  ·  label',CYAN),(6.72,3.05,5.87,1.18,'KOLUNA UTILIZADÓR','author_name  ·  gender\nauthor_facebook_id',PINK),(.72,4.46,5.78,1.18,'KOLUNA ENGAGEMENT','likes_count  ·  comments_count',MINT),(6.72,4.46,5.87,1.18,'KOLUNA TEMPU / FONTE','date  ·  facebook_url  ·  post_title',PURPLE)]:
 s.box(x,y,w,h,PANEL,STROKE); s.text(x+.2,y+.13,t,9,c,True,w=w-.4,h=.22); s.text(x+.2,y+.43,b,12,WHITE,True,w=w-.4,h=.55,valign='t',margin=0)
s.text(.77,5.94,'¹ Clean records = registros ho text ne’ebé la’ós duplicate (1,679 − 138 − 72).',9,MUTED,False,w=11.7,h=.28,italic=True); slides.append(s)
# 06 pipeline, 3x3 serpentine
s=Slide(6,'05 · PIPELINE','Pipeline: hosi dadus raw ba insight')
steps=[('01','Import Dataset'),('02','Cleaning'),('03','Preview antes/depois'),('04','Labeling'),('05','Wordlist'),('06','Decision Tree'),('07','Sentiment Analysis'),('08','Dashboard'),('09','Insight')]
positions=[]
for i,(n,t) in enumerate(steps):
 row=i//3; pos=i%3; col=pos if row!=1 else 2-pos
 x=.78+col*4.05; y=1.52+row*1.6
 positions.append((x,y))
 c=[CYAN,PINK,MINT][(i+row)%3]
 s.box(x,y,3.72,1.15,PANEL,STROKE); s.text(x+.2,y+.18,n,16,c,True,w=.56,h=.37); s.text(x+.86,y+.18,t,13,WHITE,True,w=2.65,h=.38); s.box(x+.2,y+.72,3.25,.035,c,c,False)
# arrows between boxes: use short arrow glyphs on connectors
for i in range(8):
 x,y=positions[i]; nx,ny=positions[i+1]
 if abs(ny-y)<.1: s.text(min(x,nx)+3.73,y+.37,'→',17,CYAN,True,w=.3,h=.32,align='ctr')
 else: s.text(x+1.67,y+1.18,'↓',15,CYAN,True,w=.35,h=.3,align='ctr')
s.text(.85,6.48,'IMPORT  →  LIMPEZA  →  LABEL  →  MODEL  →  DASHBOARD',10,MUTED,True,w=11.5,h=.25,align='ctr'); slides.append(s)
# 07 Method
s=Slide(7,'06 · MÉTODO','Métodu analítika iha sistema')
method=[('CLEANING','Remove emoji, URL, mention no HTML; normaliza whitespace.',CYAN),('WORDLIST','Lexicon suporta Tetum, Indonesian, Portuguese no English.',PINK),('LABELING','Komentáriu klasifika ba Positive, Neutral no Negative.',MINT),('DECISION TREE','TF-IDF transforma textu; Decision Tree halo klasifikasaun.',PURPLE),('EVALUATION','Accuracy, Precision, Recall, F1 no Confusion Matrix.',CYAN)]
for i,(t,b,c) in enumerate(method):
 x=.72+(i%3)*4.02; y=1.65+(i//3)*2.05; w=3.82 if i<3 else (5.83 if i==3 else 5.82); x=.72 if i==3 else (6.77 if i==4 else x)
 s.card(x,y,w,1.72,t,b,c,body_size=11)
s.box(.72,6.02,11.9,.55,'20183E',STROKE); s.text(.96,6.13,'Sentimentu automaticu uza wordlist; ML aprende padraun husi label sira ne’e.',10,MUTED,False,w=11.35,h=.3); slides.append(s)
# 08 System architecture and roles
s=Slide(8,'07 · SISTEMA','Sistema no papel utilizadór')
# top architecture flow
nodes=['USER','LOGIN','IMPORT CSV','CLEANING','LABELING','WORDLIST','DECISION TREE','ANALYSIS','DASHBOARD','INSIGHT']
for i,label in enumerate(nodes):
 x=.57+i*1.27; y=1.63; fill=PANEL2 if i%2==0 else PANEL; c=[CYAN,PINK,MINT,PURPLE][i%4]
 s.box(x,y,1.08,.75,fill,STROKE); s.text(x+.04,y+.15,label,8.4,c,True,w=1.0,h=.42,align='ctr')
 if i<9: s.text(x+1.09,y+.22,'›',14,MUTED,True,w=.16,h=.22,align='ctr')
# role cards
s.card(.72,2.83,5.78,2.2,'ADMIN','Jere utilizadór, dataset no wordlist; asesu ba import, cleaning, labeling no Decision Tree.',PINK,body_size=11)
s.card(6.72,2.83,5.87,2.2,'USER','Login no asesu ba dataset, sentiment analysis, dashboard, Data Visualization no Data Analysis.',CYAN,body_size=11)
s.text(.82,5.42,'DB: SQLite  ·  Tabela facebook_records  ·  sentiment_words  ·  model_training_history',10,MUTED,True,w=11.7,h=.35,align='ctr'); slides.append(s)
# 09 Dashboard
s=Slide(9,'08 · DASHBOARD','Menu no vizualizasaun dashboard')
# feature pills left
s.text(.78,1.52,'FEATURE IHA SISTEMA',9,CYAN,True,w=5.8,h=.25)
features=['Dashboard','Dataset Explorer','Cleaning','Labeling','Sentiment Analysis','Data Visualization','Data Analysis','Decision Tree','Wordlist','User Management']
for i,f in enumerate(features):
 col=i%2; row=i//2; x=.78+col*2.68; y=1.92+row*.72
 s.box(x,y,2.48,.52,PANEL,STROKE); s.text(x+.13,y+.1,f,9.4,WHITE,True,w=2.21,h=.28)
# screenshot placeholder frame
s.box(6.35,1.55,6.25,4.65,PANEL,STROKE)
s.text(6.72,1.91,'DASHBOARD FACEBOOK',10,CYAN,True,w=5.5,h=.3,align='ctr')
s.box(6.78,2.46,5.38,2.75,'09051B','536080')
s.text(7.02,3.28,'[SCREENSHOT DASHBOARD]',16,MUTED,True,w=4.9,h=.48,align='ctr')
s.text(7.0,3.86,'Screenshot real la iha iha ficheiru sistema.',10,MUTED,False,w=4.95,h=.3,align='ctr')
s.text(6.9,5.55,'Positive      Neutral      Negative',11,WHITE,True,w=5.2,h=.3,align='ctr'); slides.append(s)
# 10 insight real distribution chart + 4 insight cards
s=Slide(10,'09 · INSIGHT','Ezemplu insight ne’ebé visual sira hatudu')
s.box(.72,1.56,5.58,4.78,PANEL,STROKE); s.text(.98,1.78,'SENTIMENTU IHA DATABASE ATUAL',9,CYAN,True,w=4.9,h=.25)
# bars proportion to max 1086, labels exact
for i,(label,count,col) in enumerate([('Neutral',1086,CYAN),('Positive',592,MINT),('Negative',1,PINK)]):
 y=2.38+i*1.0; s.text(1.0,y,label,11,WHITE,True,w=1.2,h=.28); s.box(2.26,y+.04,2.94,.24,'302554','302554',False); s.box(2.26,y+.04,max(.035,2.94*count/1086),.24,col,col,False); s.text(5.32,y,str(count),11,col,True,w=.63,h=.27,align='r')
s.text(1.0,5.68,'N = 1,679  ·  fonte: facebook_records.sentiment',8.4,MUTED,False,w=4.95,h=.26)
ins=[('01 · SENTIMENTU','Distribuisaun Positive, Neutral no Negative.',CYAN),('02 · ENGAGEMENT','Likes no comments ajuda haree interasaun.',PINK),('03 · GENDER','Kompara sentimentu tuir gender.',MINT),('04 · TENDÉNSIA','Haree volume no sentimentu tuir tempu.',PURPLE)]
for i,(t,b,c) in enumerate(ins):
 row=i//2; col=i%2; x=6.62+col*3.02; y=1.68+row*2.12; s.card(x,y,2.83,1.82,t,b,c,body_size=10)
slides.append(s)
# 11 Evaluation
s=Slide(11,'10 · EVALUATION','Evaluation: oinsá atu hatene kualidade?')
s.box(.72,1.53,6.08,4.42,PANEL,STROKE); s.text(.95,1.73,'CONFUSION MATRIX · TEST SET',9,CYAN,True,w=5.4,h=.24)
# matrix columns and rows; order Positive Negative Neutral
labels=['Positive','Negative','Neutral']; x0=2.15; y0=2.35; cw=1.35; rh=.78
for j,l in enumerate(labels): s.text(x0+j*cw,y0-.38,l,8.5,MUTED,True,w=1.25,h=.28,align='ctr')
for i,(r,vals) in enumerate(zip(labels,[[108,0,4],[0,0,0],[0,0,162]])):
 y=y0+i*rh; s.text(.92,y+.15,r,8.5,MUTED,True,w=1.12,h=.28)
 for j,v in enumerate(vals):
  x=x0+j*cw; fill='183948' if v else '20183E'; s.box(x,y,1.22,.62,fill,STROKE); s.text(x,y+.11,str(v),16,MINT if v else MUTED,True,w=1.22,h=.34,align='ctr')
s.text(1.0,5.1,'Actual rows  ·  Predicted columns  ·  Order: Positive / Negative / Neutral',8,MUTED,False,w=5.6,h=.25)
s.box(7.08,1.53,5.5,2.38,'20183E',STROKE); s.text(7.35,1.75,'REPORTED METRICS',9,CYAN,True,w=4.95,h=.23)
s.text(7.38,2.18,'98.54%',22,WHITE,True,w=2.0,h=.42); s.text(9.33,2.23,'Accuracy',10,MUTED,True,w=2.4,h=.28)
s.text(7.38,2.78,'98.58%',13,MINT,True,w=1.3,h=.3); s.text(8.63,2.78,'Precision',9,MUTED,False,w=1.05,h=.3)
s.text(9.72,2.78,'98.54%',13,CYAN,True,w=1.3,h=.3); s.text(10.97,2.78,'Recall',9,MUTED,False,w=1.2,h=.3)
s.text(7.38,3.26,'98.54%',13,PURPLE,True,w=1.3,h=.3); s.text(8.63,3.26,'F1 score',9,MUTED,False,w=1.2,h=.3)
s.text(7.38,3.62,'Train 1,092   ·   Test 274',9,WHITE,True,w=4.8,h=.22)
s.box(7.08,4.18,5.5,1.77,'302554','302554'); s.text(7.32,4.36,'LIMITASAUN IMPORTANTE',9,PINK,True,w=4.95,h=.24)
s.text(7.32,4.72,'Negative: 1 total; 0 iha test set. Evaluation la valid ba klase hotu.',9,WHITE,False,w=4.92,h=.48,valign='t',margin=.01)
s.text(7.32,5.32,'Label sira mai husi wordlist; la iha label human-verified.',8.5,MUTED,False,w=4.95,h=.4,valign='t',margin=.01); slides.append(s)
# 12 conclusion
s=Slide(12,'11 · KONKLUZAUN','Konkluzaun no etapa tuirmai')
s.card(.72,1.8,5.78,1.92,'Saida mak sistema halo','Integra importasaun, preprocessing, labeling, wordlist, Machine Learning, sentiment analysis no dashboard.',CYAN,body_size=11)
s.card(6.72,1.8,5.87,1.92,'Valor ba utilizadór','Ajuda transforma komentáriu Facebook barak sai informasaun ne’ebé fasil atu analiza no komprende.',PINK,body_size=11)
s.box(.72,4.22,11.9,.92,'20183E',STROKE)
s.text(1.0,4.43,'RAW DATA',11,WHITE,True,w=1.75,h=.32,align='ctr'); s.text(2.8,4.43,'→',15,CYAN,True,w=.35,h=.32,align='ctr'); s.text(3.25,4.43,'CLEAN DATA',11,WHITE,True,w=1.85,h=.32,align='ctr'); s.text(5.2,4.43,'→',15,CYAN,True,w=.35,h=.32,align='ctr'); s.text(5.65,4.43,'LABEL',11,WHITE,True,w=1.3,h=.32,align='ctr'); s.text(7.1,4.43,'→',15,CYAN,True,w=.35,h=.32,align='ctr'); s.text(7.55,4.43,'MODEL',11,WHITE,True,w=1.5,h=.32,align='ctr'); s.text(9.3,4.43,'→',15,CYAN,True,w=.35,h=.32,align='ctr'); s.text(9.75,4.43,'INSIGHT',11,MINT,True,w=1.7,h=.32,align='ctr')
s.text(.85,5.76,'OBRIGADU!',23,WHITE,True,w=4.3,h=.54); s.text(4.45,5.89,'Pergunta no komentáriu?',12,CYAN,True,w=5.3,h=.34); slides.append(s)

# Package the editable deck with the reference's theme/master/layout, but replace its slide content
# and remove all embedded TikTok media and old slide media relationships.
with zipfile.ZipFile(BASE,'r') as zin:
    files={n:zin.read(n) for n in zin.namelist() if not n.startswith('ppt/media/') and n!='docProps/thumbnail.jpeg'}
# Replace slides and relationships, retaining matching master layouts and theme.
for i,slide in enumerate(slides,1):
    files[f'ppt/slides/slide{i}.xml']=slide.xml()
    relpath=f'ppt/slides/_rels/slide{i}.xml.rels'
    relroot=ET.Element('Relationships',{'xmlns':'http://schemas.openxmlformats.org/package/2006/relationships'})
    relroot.append(ET.Element('Relationship',{'Id':'rId1','Type':'http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout','Target':'../slideLayouts/slideLayout1.xml'}))
    files[relpath]=ET.tostring(relroot,encoding='utf-8',xml_declaration=True)
# clean document properties
if 'docProps/core.xml' in files:
    root=ET.fromstring(files['docProps/core.xml']); nsdc='{http://purl.org/dc/elements/1.1/}'; nsct='{http://purl.org/dc/terms/}'; nsx='{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}'
    for tag,val in [('title','Facebook Sentiment System Presentation'),('subject','Sistema Analítiku ba Komentáriu Facebook'),('creator','Data Science'),('description','Facebook comment sentiment analysis system')]:
        el=root.find(nsdc+tag) if tag in ('title','creator','description') else root.find(nsct+tag)
        if el is None: el=ET.SubElement(root,nsdc+tag) if tag in ('title','creator','description') else ET.SubElement(root,nsct+tag)
        el.text=val
    files['docProps/core.xml']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
# Remove custom old TikTok preview properties from extended app props
if 'docProps/app.xml' in files:
    root=ET.fromstring(files['docProps/app.xml'])
    for el in list(root):
        if el.tag.endswith('TitlesOfParts'):
            vt='{http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes}'; vec=el.find(vt+'vector')
            if vec is not None:
                for x in list(vec): x.text='Facebook Sentiment System'
    files['docProps/app.xml']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED) as zout:
    for n,b in files.items(): zout.writestr(n,b)
print(OUT)
print('slides',len(slides),'bytes',OUT.stat().st_size)


