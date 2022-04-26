from constants import API_KEY
import routeros_api
import telebot
from telebot import types
import datetime
import math

# Membuat inilisiasi bot token telegram
bot = telebot.TeleBot(API_KEY, parse_mode=None)

# Membuat koneksi API ke Mikrotik
connection = routeros_api.RouterOsApiPool('192.168.1.1', username='admin', password='admin', plaintext_login=True)

# Menampilkan pesan awal ketika mengetikkan /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, 'Welcome to telegram bot for network monitoring \n to more command available /menu')

# Membuat Botton / menu di telegram bot
@bot.message_handler(commands=["menu"])
def send_menu(message):
    markup = types.ReplyKeyboardMarkup(row_width=3)
    btn1 = types.KeyboardButton("/ping 8.8.8.8",)
    btn2 = types.KeyboardButton("/active")
    btn3 = types.KeyboardButton("/dhcp_leases")
    btn4 = types.KeyboardButton("/interface_stat")
    btn5 = types.KeyboardButton("/traffic")
    btn6 = types.KeyboardButton("/critical_log")
    btn7 = types.KeyboardButton("/reboot")
    btn8 = types.KeyboardButton("/close")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8)
    bot.reply_to(message, "What Do You Want ?", reply_markup=markup)

# Untuk menutup menu / button di telegram bot
@bot.message_handler(commands=['close'])
def send_close(message):
    markup = types.ReplyKeyboardRemove(selective=False)
    bot.reply_to(message, 'Good Bye!', reply_markup=markup)

# Membatasi mengirim photo dan sticker di telegram
@bot.message_handler(content_types=["photo", "sticker" ])
def send_content(message):
    bot.reply_to(message, "That's not a text message!")

# Mengecek dhcp lease mikrotik untuk mengetahui client terkoneksi ke jaringan
@bot.message_handler(commands=['dhcp_leases'])
def send_status(message):
    api = connection.get_api()
    stat_dhcp = api.get_resource('ip/dhcp-server/lease')
    show_stat_dhcp = stat_dhcp.get()
    user = ''
    for i, x in enumerate(show_stat_dhcp):
        dhcpaddr = x['address']
        dhcphost = x['mac-address']

        user = user + str(i) + ". "+ dhcpaddr + " : "+ dhcphost +'\n'
    bot.reply_to(message, user)

# Mengecek status interface ke Access point apa status UP / Down
@bot.message_handler(commands=['interface_stat'])
def send_int_stat(message):
    api = connection.get_api()
    interface2 = api.get_resource('interface/')
    sw_interface2 = interface2.get(name='ether2')

    interface3 = api.get_resource('interface/')
    sw_interface3 = interface3.get(name='ether3')

    for x in sw_interface2:
        if(x['running']=='true'):
            stat1 = 'Ethernet2 : Up'
        else:
            stat1 = 'Ethernet2 : Down'

    for x in sw_interface3:
        if(x['running']=='true'):
            stat2 = 'Ethernet3 : Up'
        else:
            stat2 = 'Ethernet3 : Down'

    stat = stat1 + "\n" + stat2
    bot.reply_to(message, stat)
    connection.disconnect()

# Mengecek kondisi jaringan dengan ping default ping ke 8.8.8.8
@bot.message_handler(commands=['ping'])
def send_ping(message):
    api = connection.get_api()
    dict_ping = {'address': {} , 'count': b'1' }
    ips = message.text.split(' ')
    ip = ips[1]   
    conv_ip = bytes(ip,'utf-8')
    dict_ping['address']= conv_ip
    cmd_ping = api.get_binary_resource('/').call('ping', dict_ping)

    for x in cmd_ping:
        try:
            avg_rtt= x['avg-rtt']
        except:
            avg_rtt= "Request Time out"

        bot.reply_to(message, avg_rtt)
    connection.disconnect()

# Monitoring Traffic ether2 Mikrotik
@bot.message_handler(commands=['traffic'])
def send_bandwidth(message):
    api = connection.get_api()
    int_mon_traf = api.get_resource('interface/')
    sh_int_mon_traf = int_mon_traf.get(name="ether2")

    for x in sh_int_mon_traf:
        downlink = x['tx-byte']
        downlink_a = int(downlink)
        downlink_b = downlink_a/(1024**1)
        downlink_c = math.ceil(downlink_b)
        download = str(downlink_c)

        uplink = x['rx-byte']
        uplink_a = int(uplink)
        uplink_b = uplink_a/(1024**1)
        uplink_c = math.ceil(uplink_b)
        upload = str(uplink_c)

        download = "rx-byte" + ": " + download +" " +"kbps"
        upload = "tx-Byte" + ": " + upload +" " +"kbps"

        data = ("""{}\n{}""".format(download, upload))

    bot.reply_to(message, data)
    connection.disconnect()

# Melakukan Reboot Mikrotik
@bot.message_handler(commands=['reboot'])
def send_reboot(message):
    api = connection.get_api()
    api.get_binary_resource('/').call('system/reboot')
    bot.reply_to(message, 'Successfully reboot')
    connection.disconnect()

# Mengecek critical log pada mikrotik di (/log)
@bot.message_handler(commands=['critical_log'])
def send_log(message):
    api = connection.get_api()
    stat_log = api.get_resource('log/')
    show_stat_log = stat_log.get()
    index=1
    limit=9
    log = ''
    for index, x in enumerate(show_stat_log):
        logtopic = x['topics']
        if logtopic == "system,error,critical":
            log = log + str(index+1)+" . " + x['message'] + "\n"
            if index == limit:
                break
        else:
            False
    if (log == ''):
        bot.reply_to(message, "Tidak ada data critical Log ditemukan!")
    else:
        bot.reply_to(message, log)
    connection.disconnect()

# Mengecek User Hotspot Aktive mikrotik di (/ip/hotspot/active)
@bot.message_handler(commands=['active'])
def send_active(message):
    api = connection.get_api()
    stat_active = api.get_resource('ip/hotspot/active/')
    show_stat_active = stat_active.get()
    hsdata = ''
    for i, x in enumerate(show_stat_active):
        hsuser = x['user']
        hsaddr = x['address']
        hsdata = hsdata + str(i) + ". User : "+ hsuser + "\n    Address : "+ hsaddr +'\n'
    if (hsdata !=''):
        bot.reply_to(message, hsdata)
    else:
        bot.reply_to(message, "Tidak ada user hotspot active ditemukan!")
    connection.disconnect()

print('Telegram bot running ...')
print(datetime.datetime.now())

bot.polling()
bot.infinity_polling(timeout=25, long_polling_timeout = 5)