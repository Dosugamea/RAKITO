from bottle import run,route,response,request,static_file,redirect
from bottle import error
from bottle import jinja2_template as template
import bottle
import sqlite3
import random
import json
import os
import datetime
import glob

class SQLer(object):
    def __init__(self,filename):
        self.db = sqlite3.connect(filename, check_same_thread=False)
        self.conn = self.db.cursor()
        
    def get(self,sql,params=None):
        if params != None:
            self.conn.execute(sql,params)
        else:
            self.conn.execute(sql)
        return self.conn.fetchall()
        
    def edit(self,sql,params=None):
        if params != None:
            self.conn.execute(sql,params)
        else:
            self.conn.execute(sql)
        self.db.commit()
        return True
        
class IDGenerator(object):
    ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"

    def __init__(self, length=8):
        self._alphabet_length = len(self.ALPHABET)
        self._id_length = length

    def _encode_int(self, n):
        # Adapted from:
        #   Source: https://.com/a/561809/1497596
        #   Author: https://.com/users/50902/kmkaplan

        encoded = ''
        while n > 0:
            n, r = divmod(n, self._alphabet_length)
            encoded = self.ALPHABET[r] + encoded
        return encoded

    def generate_id(self):
        """Generate an ID without leading zeros.

        For example, for an ID that is eight characters in length, the
        returned values will range from '10000000' to 'zzzzzzzz'.
        """

        start = self._alphabet_length**(self._id_length - 1)
        end = self._alphabet_length**self._id_length - 1
        return self._encode_int(random.randint(start, end))
        
db = SQLer("concept.db")
idgen = IDGenerator(8)


# 翻訳ファイルを1つにまとめる
trans_all = {}
# まずJSONから読み出し
for t in glob.glob("./views/translate/*"):
    keyName = os.path.split(t)[1].replace(".json","")
    with open(t,"r",encoding="utf-8-sig") as f:
        trans_all.update(json.loads(f.read()))
# 次にDBから呼び出し
data = db.get("SELECT search_id,search_name,search_name_en FROM search_head")
for d in data:
    trans_all.update({"tag_%s"%(d[0]):{"ja":d[1],"en":d[2]}})
trans_all = json.dumps(trans_all)

'''
 API: ユーザー用
'''

@route("/api/ranking",method="GET")
def shop_ranking():
    data = db.get("SELECT shop_id,shop_name,shop_detail FROM shop LIMIT = 5 ORDER BY shop_lastupdate")
    return str(resp)
@route("/api/tag_search",method="GET")
def tag_search_shop():
    sid = request.query.get('id')
    if sid == None:
        return {"status":"ng"}
    head = db.get("SELECT search_name,search_detail,(SELECT COUNT(shop_id) FROM search_body WHERE search_id = ?) FROM search_head WHERE search_id = ?",[sid,sid])[0]
    resp = {
        "status":"ok",
        "query":head[0],
        "detail":head[1],
        "cnt":head[2],
        "datas":[]
    }
    shops = db.get("SELECT shop_id,shop_name,shop_detail FROM search_body natural join search_head natural join shop WHERE search_id = ?",[(sid)])
    for s in shops:
        tags = db.get("SELECT group_concat(search_id||':'||search_name) FROM search_body natural join search_head natural join shop WHERE shop_id = ?",[s[0]])
        if len(s[2]) > 50:
            resp["datas"].append({
                "id":s[0],
                "name":s[1],
                "detail":s[2][:50]+"...",
                "tags": [s.split(":") for s in tags[0][0].split(",")]
            })
        else:
            resp["datas"].append({
                "id":s[0],
                "name":s[1],
                "detail":s[2],
                "tags": [s.split(":") for s in tags[0][0].split(",")]
            })
    return json.dumps(resp)
@route("/api/word_search",method="GET")
def word_search_shop():
    stype = request.query.t
    sid = request.query.q
    if sid == None:
        return {"status":"ng"}
    cnt =  db.get("SELECT (SELECT COUNT(shop_id) FROM shop WHERE shop_name like ?) FROM shop WHERE shop_name like ?",["%"+sid+"%","%"+sid+"%"])
    if cnt == []:
        cnt = 0
    else:
        cnt = cnt[0][0]
    resp = {
        "status":"ok",
        "query":sid,
        "cnt": cnt,
        "datas":[]
    }
    shops = db.get("SELECT DISTINCT shop_id,shop_name,shop_detail FROM search_body natural join search_head natural join shop WHERE shop_name like ?",["%"+sid+"%"])
    for s in shops:
        tags = db.get("SELECT group_concat(search_id||':'||search_name) FROM search_body natural join search_head natural join shop WHERE shop_id = ?",[s[0]]) 
        if len(s[2]) > 50:
            resp["datas"].append({
                "id":s[0],
                "name":s[1],
                "detail":s[2][:50]+"...",
                "tags": [{"id":s.split(":")[0],"name":s.split(":")[1]} for s in tags[0][0].split(",")]
            })
        else:
            resp["datas"].append({
                "id":s[0],
                "name":s[1],
                "detail":s[2],
                "tags": [{"id":s.split(":")[0],"name":s.split(":")[1]} for s in tags[0][0].split(",")]
            })
    return json.dumps(resp)

@route("/api/shop",method="GET")
def shop_info():
    try:
        sid = request.query.get('id')
        data = db.get("SELECT *,(SELECT COUNT(shop_id) FROM menu WHERE shop_id = ?) AS menus FROM shop WHERE shop_id = ?",[sid,sid])
        resp = {
            "status":"ok",
            "name": data[0][1],
            "detail": data[0][2],
            "gps1": data[0][3],
            "gps2": data[0][4],
            "addr": data[0][5],
            "tel": data[0][6],
            "km": data[0][7],
            "time": data[0][8],
            "sun": "○" if data[0][9] == 1 else "×",
            "mon": "○" if data[0][10] == 1 else "×",
            "tue": "○" if data[0][11] == 1 else "×",
            "wed": "○" if data[0][12] == 1 else "×",
            "thu": "○" if data[0][13] == 1 else "×",
            "fri": "○" if data[0][14] == 1 else "×",
            "sat": "○" if data[0][15] == 1 else "×",
            "time_detail": data[0][16],
            "last_update": data[0][17]
        }
        return json.dumps(resp)
    except:
        return json.dumps({"status":"error"})

@route("/api/menu",method="GET")
def shop_menu():
    try:
        sid = request.query.get('menu_id')
        data = db.get("SELECT * FROM shop WHERE menu_id = ?",[sid])
        return resp
    except:
        return "404 メニューデータが存在しません"
        
@route("/api/img",method="GET")
def shop_img():
    try:
        sid = request.query.get('id')
        num = request.query.get('num')
        if os.path.exists("img/%s/%s.png"%(sid,num)):
            return static_file("%s/%s.png"%(sid,num), root="img/")
        return static_file("not-found.png", root="img/")
    except:
        return static_file("not-found.png", root="img/")

@route("/api/pdf",method="GET")
def shop_pdf():
    try:
        #sid = request.query.get('id')
        #ptp = request.query.get('pdf_type')
        return static_file("1_1.pdf"%(sid,ptp), root="pdf/")
        '''
        if int(ptp) == 1:
            return static_file("1_1.pdf", root="pdf/")
        else:
            return static_file("1_2.pdf", root="pdf/")
        '''
    except:
        return "404 PDFファイルが存在しませんでした。"

@route("/api/review",method="GET")
def get_review():
    try:
        sid = request.query.get('id')
        data = db.get("SELECT account_name,review_date,review_rate,review_title,review_contents FROM review NATURAL LEFT JOIN account WHERE shop_id = ?;",[sid])
        resp = {"datas":[]}
        for d in data:
            nd = {
                "name":d[0],
                "date":d[1],
                "rate": "".join(["★" for i in range(int(d[2]))]),
                "title":d[3],
                "content":d[4]
            }
            resp["datas"].append(nd)
        return json.dumps(resp)
    except:
        return json.dumps({"status":"error"})
    
@route("/api/review",method="POST")
def add_review():
    token = request.get_cookie('token', secret="some-secret-key")
    token = token.split(",,,")
    sid = request.forms.shop_id
    title = request.forms.email
    content = request.forms.password
    rate = request.forms.phone
    date = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    data = db.get("SELECT account_name,account_id FROM account WHERE account_name = ? AND account_password = ?",[token[0],token[1]])
    if len(data) == 1:
        db.edit("INSERT INTO `review`(`account_id`,`shop_id`,`review_title`,`review_contents`,`review_rate`,`review_date`) VALUES (?,?,?,?,?,?);",[token[0],sid,title,content,rate,date])
        redirect("shop.html?id=%s"%(sid))
    else:
        raise Exception("Login error")
        
@route("/api/user",method="GET")
def user_info():
    try:
        aid = request.query.get('k')
        data = db.get("SELECT * FROM account WHERE account_name = ?",[aid])[0]
        return json.dumps({"id":data[0],"name":data[1],"phone":data[2],"mail":data[3]})
    except:
        return {"status":"err"}

@route("/api/logout",method="GET")
def user_logout():
    response.set_cookie("isLogined", "0",path="/")
    response.set_cookie("userName", "",path="/")
    response.set_cookie("token","dead",secret="some-secret-key",path="/")
    redirect("/index.html")

@route("/api/register",method="POST")
def register_user():
    email = request.forms.email
    passwd = request.forms.password
    phone = request.forms.phone
    name = request.forms.name
    if email != "" and passwd != ""\
    and name != "" and phone != "":
        is_exist = db.get("SELECT 'T' FROM account WHERE account_email = ?",[email])
        if len(is_exist) != 0:
            return "そのメールアドレスは既に使用されています\nメールアドレスを確認してもう一度やり直してください\nThe email is already registered.\nPlease check address and try again."
        db.edit("INSERT INTO account ('account_name','account_phone','account_email','account_password') VALUES (?,?,?,?)",[name,phone,email,passwd])
        redirect("/login.html?stat=1")
    else:
        redirect("/register.html?stat=2")

@route("/api/changelog",method="GET")
def get_changelog():
    return [["19/05/29","更新履歴機能を実装しました"]]
    
@route("/api/changelog",method="POST")
def add_changelog():
    return "ERROR"
        
@route("/api/translate.json",method="GET")
def translate():
    return trans_all

@route("/api/login",method="POST")
def login():
    maila = request.forms.mail
    passw = request.forms.passw
    data = check_login(maila,passw)
    if data[0]:
        response.set_cookie("isLogined", "1",path="/")
        response.set_cookie("userName", data[1][0][0],path="/")
        response.set_cookie("token",str(data[1][0][0]+",,,"+passw),secret="some-secret-key",path="/")
        redirect("/index.html")
    else:
        response.set_cookie("isLogined", "0",path="/")
        response.set_cookie("token","dead",secret="some-secret-key",path="/")
        redirect("/login.html?stat=2")
    
def check_login(email, password):
    data = db.get("SELECT account_name,account_id FROM account WHERE account_email = ? AND account_password = ?",[email,password])
    if len(data) == 1:
        return True,data
    else:
        return False,"Guest"

'''
 API: 管理用
'''

@route("/api/admin/shop_add",method="POST")
def shop_add():
    '''
    req_form = dict(request.params)
    if req_form.keys() != ("shop_name","shop_detail","","","","",):
        return "指定されたパラメータ数が不適切です"
    '''
    shop_name = request.forms.name
    shop_dtil = request.forms.dtil
    shop_loc1 = request.forms.loc1
    shop_loc2 = request.forms.loc2
    shop_addr = request.forms.addr
    shop_km   = request.forms.km
    shop_time = request.forms.time
    shop_tdtl = request.forms.tdtl
    shop_mon  = request.forms.b_mon
    if shop_mon == "on":
        shop_mon = 1
    else:
        shop_mon = 0
    shop_tue  = request.forms.b_tue
    if shop_tue == "on":
        shop_tue = 1
    else:
        shop_tue = 0
    shop_wed  = request.forms.b_wed
    if shop_wed == "on":
        shop_wed = 1
    else:
        shop_wed = 0
    shop_thu  = request.forms.b_thu
    if shop_thu == "on":
        shop_thu = 1
    else:
        shop_thu = 0
    shop_fri  = request.forms.b_fri
    if shop_fri == "on":
        shop_fri = 1
    else:
        shop_fri = 0
    shop_sat  = request.forms.b_sat
    if shop_sat == "on":
        shop_sat = 1
    else:
        shop_sat = 0
    shop_sun  = request.forms.b_sun
    if shop_sun == "on":
        shop_sun = 1
    else:
        shop_sun = 0
    shop_reg  = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    db.edit('INSERT INTO shop ("shop_name","shop_detail","shop_location1","shop_location2","shop_address","shop_km","shop_time","shop_sun","shop_mon","shop_tue","shop_wed","shop_thu","shop_fri","shop_sat","shop_time_detail","shop_lastupdate") VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',[shop_name,shop_dtil,shop_loc1,shop_loc2,shop_addr,shop_km,shop_time,shop_sun,shop_mon,shop_tue,shop_wed,shop_thu,shop_fri,shop_sat,shop_tdtl,shop_reg])
    shop_id = db.get("SELECT MAX(shop_id) FROM shop")[0][0]
    tag = "タグ未登録"
    #まずそのタグが存在しているか確認
    data = db.get("SELECT search_id FROM search_head WHERE search_name = ?",[tag])
    if len(data) == 1:
        #存在してるならID指定
        tag_id = data[0][0]
    else:
        db.edit("INSERT INTO search_head (search_name) VALUES (?)",[tag])
        tag_id = db.get("SELECT MAX(search_id) FROM search_head")[0][0]
    #店にタグ登録
    db.edit("INSERT INTO search_body (search_id,shop_id) VALUES (?,?)",[tag_id,shop_id])
    redirect("/admin/shop_manager.html")
    
@route("/api/admin/shop_remove",method="POST")
def shop_remove():
    shop_id = request.forms.get('shop_id')
    db.edit("DELETE FROM Shop WHERE = ?",[shop_id])
    return "200"

@route("/api/admin/tag_add",method="POST")
def search_tag_add():
    shop_id = request.forms.get('shop_id')
    tag = request.forms.tag_id
    #まずそのタグが存在しているか確認
    data = db.get("SELECT search_id FROM search_head WHERE search_name = ?",[tag])
    if len(data) == 1:
        #存在してるならID指定
        tag_id = data[0][0]
    else:
        db.edit("INSERT INTO search_head (search_name) VALUES (?)",[tag])
        tag_id = db.get("SELECT MAX(search_id) FROM search_head")[0][0]
    #店にタグ登録
    db.edit("INSERT INTO search_body (search_id,shop_id) VALUES (?,?)",[tag_id,shop_id])
    return "タグを追加しました"

@route("/api/admin/tag_remove",method="POST")
def search_tag_remove():
    shop_id = request.forms.get('shop_id')
    tag = request.forms.tag_id
    data = db.get("SELECT search_id FROM search_head")
    if len(data) == 1:
        db.edit("DELETE FROM search_body WHERE search_id = ?",[data[0]])
        return "タグの削除に成功しました"
    else:
        return "削除できませんでした"
    
@route("/api/admin/issue_account",method="POST")
def issue_account_code():
    email = request.forms.get('email')
    is_exist =  db.get("SELECT 'T' FROM register WHERE register_email = ?",[email])
    if len(is_exist) != 0:
        return "The email is already exists"
    if email != None:
        reg_key = str(idgen.generate_id())
        db.edit("INSERT INTO register ('register_key','register_issue_date','register_email') VALUES (?,?,?);",[reg_key,datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'),email])
        return str(reg_key)
    else:
        return "Invalid Token"

    
'''
 デフォルトレンダー
'''

@route('/admin/<filename:path>')
def render_index(filename):
    return static_file(filename, root="views/admin/")

@route('/<page:re:.+.html>')
def render_page(page):
    page = page.replace("html","j2")
    if page == "index.j2":
        qd = dict(request.query).keys()
        if "s" in qd:
            db.edit("INSERT INTO search_head (search_name) VALUES (?)")
    if os.path.exists("views/"+page):
        return template(page)
    return "<html><head><title>そのページは存在しません</title></head><body><center>404 そのページは存在しません</center></body></html>"

@route('/')
def render_index():
    return render_page("index.html")
    
@route('/<filename:path>')  
def render_default(filename):
    return static_file(filename, root="views/")

if __name__ == "__main__":
    run(host="localhost", port=8080,reload=True)