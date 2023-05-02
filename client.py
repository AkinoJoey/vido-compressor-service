from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import socket
import os
import json
import threading

class Client:
    def __init__(self):
        self.BUFFER_SIZE = 4096
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket_connected = False
        self.server_address = "127.0.0.1"
        self.server_port = 9999
        self.file_path = None
        self.menu_info = {
            "file_name": None,
            "file_extension": None,
            "main_menu": None,
            "option_menu":None
        }
        
    def connect(self,event):
        self.sock.connect((self.server_address, self.server_port))
        self.socket_connected = True

        self.send_menu_info(event)
    
    def send_menu_info(self,event):
        print("sending menu info ...")
        json_file = json.dumps(self.menu_info)
        json_file_bytes = json_file.encode("utf-8")

        header = self.protocol_make_header(len(json_file_bytes))
        self.sock.sendall(header)
        self.sock.sendall(json_file_bytes)

        self.wait_for_video_send(event)
    
    def protocol_make_header(self,data_length):
        STREAM_RATE = 4
        return data_length.to_bytes(STREAM_RATE,"big")

    def wait_for_video_send(self,event):
        message_from_server_length = self.protocol_extract_data_length_from_header()
        message_from_server = self.sock.recv(message_from_server_length).decode("utf-8")
        print(message_from_server)

        if message_from_server == "need":
            self.send_video(event)
        elif message_from_server == "No need":
            self.wait_to_convert(event)
        else:
            raise ValueError("error")
        
    def protocol_extract_data_length_from_header(self):
        STREAM_RATE = 4
        return int.from_bytes(self.sock.recv(STREAM_RATE),"big")
    
    def send_video(self,event):
        print("Sending video...")
        print(self.file_path)
        STREAM_RATE = 4096
        
        with open(self.file_path, "rb") as video:
            video.seek(0, os.SEEK_END)
            data_size = video.tell()
            video.seek(0,0)
            header = self.protocol_make_header(data_size)
            self.sock.sendall(header)
            
            data = video.read(STREAM_RATE)
            
            while data:
                print("sending...")
                self.sock.send(data)
                data = video.read(STREAM_RATE)
            
        print("Done sending...")
        
        self.wait_to_convert(event)
        
    def wait_to_convert(self,event):
        message_length = self.protocol_extract_data_length_from_header()
        message = self.sock.recv(message_length).decode("utf-8")
        if message == "done":
            event.set()
    
    def tell_server_want_to_download(self,event):
        message_bytes = "download".encode("utf-8")
        header = self.protocol_make_header(len(message_bytes))
        self.sock.sendall(header)
        self.sock.sendall(message_bytes)
        
        print(threading.active_count())
        print(threading.current_thread())
        
        self.download_video(event)
        
    def download_video(self,event):
        print(threading.active_count())
        print(threading.current_thread())

        STREAM_RATE = 4096
        data_length = self.protocol_extract_data_length_from_header()
        download_dir_path = os.path.join(os.getenv('USERPROFILE'), 'Downloads') if os.name  == "nt" else os.path.expanduser('~/Downloads')
        download_video_full_path_without_extension = os.path.join(download_dir_path,self.menu_info["file_name"])
        file_extension = self.menu_info["file_extension"]
        file_name =  self.check_for_same_name_and_rename(download_video_full_path_without_extension,file_extension)
        
        try:
            with open(file_name, "xb") as video:
                print("downloading video...")
                while data_length > 0:
                    data = self.sock.recv(data_length if data_length <= STREAM_RATE else STREAM_RATE)
                    video.write(data)
                    data_length -= len(data)
                    # print(data_length)

            print("Done downloading ...")
            event.set()

        except Exception as e:
            print("Download error:" + str(e))
    
    def check_for_same_name_and_rename(self,download_video_full_path_without_extension,file_extension):
        file_name = download_video_full_path_without_extension + file_extension
        number_for_file_name_overwrite = 1

        while os.path.isfile(file_name):
                file_name = download_video_full_path_without_extension + " " + str(f"({number_for_file_name_overwrite})") + file_extension
                number_for_file_name_overwrite += 1
                
        return file_name
                
class ViewController:
    def __init__(self,client):
        self.root = Tk()
        self.client = client
        self.file_name_for_display = StringVar()

    def create_main_manu_page(self):
        # rootの構成
        # サイズを決める
        self.root.geometry("620x220")
        #　リサイズをFalseに設定 
        self.root.resizable(False, False)
        self.root.title("Main Menu")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # mainframeの作成
        mainframe = ttk.Frame(self.root)
        mainframe.grid(column=0, row=0,sticky=(N, W, E, S))
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)
        mainframe.rowconfigure(1, weight=1)
        
        # 上半分のフレーム
        upper_half_frame = ttk.Frame(mainframe)
        upper_half_frame.grid(column=0, row=0,sticky=(N, W, E, S))
        upper_half_frame.columnconfigure(0, weight=1)
        upper_half_frame.rowconfigure(0, weight=1)
        
        # 下半分のフレーム
        lower_half_frame = ttk.Frame(mainframe)
        lower_half_frame.grid(column=0,row=1,sticky=(N, W, E, S))
        lower_half_frame.columnconfigure(0, weight=1)
        lower_half_frame.columnconfigure(1, weight=1)
        lower_half_frame.columnconfigure(2, weight=1)
        lower_half_frame.rowconfigure(0, weight=1)
        lower_half_frame.rowconfigure(1, weight=1)
        
        # 動画選択ボタン
        upload_btn_frame = ttk.Frame(upper_half_frame)
        upload_btn_frame.grid(column=0, row=0,sticky=(N,W,E,S))
        upload_btn_frame.columnconfigure(0,weight=1)
        upload_btn_frame.rowconfigure(0,weight=2)
        upload_btn_frame.rowconfigure(1,weight=1)
        ttk.Button(upload_btn_frame, text="選択" ,command=self.prompt_video_file).grid(column=0, row=0,sticky=S)

        # 選択した動画名の表示部分
        file_name_label = ttk.Label(upload_btn_frame, textvariable=self.file_name_for_display)
        file_name_label.grid(column=0, row=1,sticky=N)
        
        # 圧縮ボタンの部分
        compress_frame = ttk.Frame(lower_half_frame)
        compress_frame.grid(column=0, row=0)
        compress_frame.columnconfigure(0, weight=1)
        compress_frame.rowconfigure(0, weight=1)
        ttk.Button(compress_frame,text="圧縮",command=lambda:[
            self.confirm_selected_video("compress"),
            self.set_main_menu_dict("compress")
            ]).grid(column=0, row=0)
        
        # # 解像度ボタンの部分
        resolution_frame = ttk.Frame(lower_half_frame)
        resolution_frame.grid(column=1, row=0)
        ttk.Button(resolution_frame,text="解像度",command=lambda:[
            self.confirm_selected_video("resolution"),
            self.set_main_menu_dict("resolution")
        ]).grid(column=0, row=0)
        
        # # 縦横比ボタンの部分
        ratio_frame = ttk.Frame(lower_half_frame)
        ratio_frame.grid(column=2, row=0)
        ttk.Button(ratio_frame,text="縦横比").grid(column=0, row=0)
        
        # # to Audioボタンの部分
        to_audio_frame = ttk.Frame(lower_half_frame)
        to_audio_frame.grid(column=0, row=1)
        ttk.Button(to_audio_frame,text="to Audio").grid(column=0, row=0)
        
        # # WEBMボタンの部分
        gif_webm_frame = ttk.Label(lower_half_frame)
        gif_webm_frame.grid(column=1, row=1)
        ttk.Button(gif_webm_frame, text="to GIF").grid(column=0, row=0)

        # # WEBMボタンの部分
        gif_webm_frame = ttk.Label(lower_half_frame)
        gif_webm_frame.grid(column=2, row=1)
        ttk.Button(gif_webm_frame, text="to WEBM").grid(column=0, row=0)

        self.root.mainloop()
    
    def prompt_video_file(self):
        file_path = filedialog.askopenfilename(
            title = "動画ファイルを選択",
            initialdir= "./"
        )

        # 拡張子なしのファイル名
        file_name_with_extension = os.path.basename(file_path)
        file_name_without_extension = os.path.splitext(os.path.basename(file_path))[0]
        file_extension = os.path.splitext(file_name_with_extension)[1]

        self.set_file_path(file_path)
        self.set_file_name_dict(file_name_without_extension)
        self.set_file_extension_dict(file_extension)
        self.display_file_name(file_name_with_extension)
    
    def confirm_selected_video(self,selected_main_manu):
        if self.file_name_for_display.get() == "":
            messagebox.showerror(title="error",message="ファイルを選択してください")
        else:
            if selected_main_manu == "compress":
                self.create_compress_option_window()
            elif selected_main_manu == "resolution":
                self.create_resolution_option_window()
    
    def set_main_menu_dict(self, main_menu):
        self.client.menu_info["main_menu"] = main_menu

    def set_file_path(self, file_path):
        self.client.file_path = file_path
        
    def set_file_name_dict(self,file_name):
        self.client.menu_info["file_name"] = file_name
    
    def set_file_extension_dict(self,file_extension):
        self.client.menu_info["file_extension"] = file_extension
    
    def display_file_name(self, file_name):
        self.file_name_for_display.set(file_name)
        
        
    def create_new_window(self,title):
        option_window = Toplevel(self.root)
        option_window.title(title)
        option_window.geometry("420x220")
        option_window.resizable(False,False)
        option_window.columnconfigure(0, weight=1)
        option_window.rowconfigure(0, weight=1)
        
        return option_window
    
    def create_new_window(self,title):
        option_window = Toplevel(self.root)
        option_window.title(title)
        option_window.geometry("420x220")
        option_window.resizable(False,False)
        option_window.columnconfigure(0, weight=1)
        option_window.rowconfigure(0, weight=1)
        
        return option_window
 
            
    def create_compress_option_window(self):
        # option_windowの作成
        option_window = self.create_new_window("圧縮レベル")

        # mainframeの作成
        mainframe = ttk.Frame(option_window)
        mainframe.grid(column=0, row=0,sticky=(N, W, E, S))
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)
        mainframe.rowconfigure(1, weight=1)
        mainframe.rowconfigure(2, weight=1)
        mainframe.rowconfigure(3, weight=1)

        # radio button
        compress_level = StringVar(value="middle")
        high = ttk.Radiobutton(mainframe, text="high", variable=compress_level, value="high")
        high.grid(column=0,row=0)
        middle = ttk.Radiobutton(mainframe, text="middle", variable=compress_level, value="middle")
        middle.grid(column=0, row=1)
        low = ttk.Radiobutton(mainframe, text="low", variable=compress_level, value="low")
        low.grid(column=0, row=2)

        # start button
        ttk.Button(mainframe, text="start",command=lambda:[
            self.set_option_menu_dict(compress_level.get()),
            self.start_to_convert(option_window)
            ]).grid(column=0, row=3)

        # main manuの操作ができないように設定して、フォーカスを新しいウィンドウに移す
        option_window.grab_set()
        option_window.focus_set()
    
    def create_resolution_option_window(self):
        option_window = self.create_new_window("解像度を選択する")

        mainframe = ttk.Frame(option_window)
        mainframe.grid(column=0, row=0,sticky=(N, W, E, S))
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)
        mainframe.rowconfigure(1, weight=1)
        mainframe.rowconfigure(2, weight=1)

        # # 左半分
        # left_frame = ttk.Frame(mainframe)
        # left_frame.grid(column=0,row=0,sticky=(N,W,E,S))
        # left_frame.columnconfigure(0,weight=1)
        # left_frame.rowconfigure(0,weight=1)
        # left_frame.rowconfigure(1,weight=1)
        # left_frame.rowconfigure(2,weight=1)
        # format_label = ttk.Label(left_frame, text="フォーマット")
        # format_label.grid(column=0, row=0)
        # resolution_label = ttk.Label(left_frame, text="解像度")
        # resolution_label.grid(column=0,row=1)

        # # 右半分
        # right_frame = ttk.Frame(mainframe)
        # right_frame.grid(column=1, row=0,sticky=(N,W,E,S))
        # right_frame.columnconfigure(0, weight=1)
        # right_frame.rowconfigure(0, weight=1)
        # right_frame.rowconfigure(1, weight=1)
        # right_frame.rowconfigure(2, weight=1)
        # format_textvar = StringVar()
        # format_list= ("720p","1080p","4K","カスタム")
        # format_combobox = ttk.Combobox(right_frame,textvariable=format_textvar,values=format_list,justify=CENTER,state="readonly")
        # format_combobox.grid(column=0,row=0)
        # format_combobox.set(format_list[0])        

        # resolution_frame = ttk.Frame(right_frame)
        # resolution_frame.grid(column=0, row=1,sticky=(N,W,E,S))
        # resolution_frame.rowconfigure(0, weight=1)
        # resolution_frame.columnconfigure(0, weight=3)
        # resolution_frame.columnconfigure(1, weight=1)
        # resolution_frame.columnconfigure(2, weight=3)

        # width = StringVar()
        # height = StringVar()
        # width_entry = ttk.Entry(resolution_frame,textvariable=width)
        # width_entry.grid(column=0,row=0)
        # height_entry = ttk.Entry(resolution_frame,textvariable=height)
        # height_entry.grid(column=2,row=0)
        # x = ttk.Label(resolution_frame, text= "x")
        # x.grid(column=1,row=0)

        # # start button
        # ttk.Button(right_frame, text="start").grid(column=0, row=2)
        

        # フォーマット部分
        format_frame = ttk.Frame(mainframe)
        format_frame.grid(column=0, row=0,sticky=(N, W, E, S))
        format_frame.columnconfigure(0, weight=1)
        format_frame.columnconfigure(1, weight=1)
        format_frame.rowconfigure(0,weight=1)

        format_label = ttk.Label(format_frame, text="フォーマット")
        format_label.grid(column=0, row=0)
        
        format_textvar = StringVar()
        format_list= ("720p","1080p","4K","カスタム")
        format_combobox = ttk.Combobox(format_frame,textvariable=format_textvar,values=format_list,justify=CENTER,state="readonly",width=10)
        format_combobox.grid(column=1,row=0,sticky=W)
        format_combobox.set(format_list[0])

        # 解像度の部分
        resolution_frame = ttk.Frame(mainframe)
        resolution_frame.grid(column=0, row=1, sticky=(N,W,E,S))
        resolution_frame.columnconfigure(0, weight=1)
        resolution_frame.columnconfigure(1, weight=1)
        resolution_frame.columnconfigure(2, weight=1)
        resolution_frame.columnconfigure(3, weight=1)
        resolution_frame.rowconfigure(0, weight=1)

        resolution_label = ttk.Label(resolution_frame, text="解像度")
        resolution_label.grid(column=0, row=0)
        width = StringVar()
        height = StringVar()
        width_entry = ttk.Entry(resolution_frame,textvariable=width,width=10)
        width_entry.grid(column=1,row=0)
        height_entry = ttk.Entry(resolution_frame,textvariable=height,width=10)
        height_entry.grid(column=3,row=0)
        x = ttk.Label(resolution_frame, text= "x")
        x.grid(column=2,row=0)

        # # start button
        ttk.Button(mainframe, text="start").grid(column=0, row=2)

    def create_new_window(self,title):
        option_window = Toplevel(self.root)
        option_window.title(title)
        option_window.geometry("420x220")
        option_window.resizable(False,False)
        option_window.columnconfigure(0, weight=1)
        option_window.rowconfigure(0, weight=1)
        
        return option_window
    
    
    def set_option_menu_dict(self, option_menu):
        self.client.menu_info["option_menu"] = option_menu

    def start_to_convert(self,option_window):
        option_window.destroy()
        prosessing_window = self.display_progressbar("処理中")

        event = threading.Event()
        
        if self.client.socket_connected == False:
            connect_thread = threading.Thread(target=self.client.connect,args=[event])
            connect_thread.start()
        else:
            connected_thread = threading.Thread(target=self.client.send_menu_info,args=[event])
            connected_thread.start()

        create_compress_option_window_thread = threading.Thread(target=self.create_download_window,args=[prosessing_window,event])
        create_compress_option_window_thread.start()
        
    def display_progressbar(self,title):
        prosessing_window = self.create_new_window(title)
        
        mainframe = ttk.Frame(prosessing_window,padding=50)
        mainframe.grid(column=0, row=0,sticky=(N, W, E, S))
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)
        
        progressbar = ttk.Progressbar(mainframe,length=200,orient=HORIZONTAL,mode='indeterminate')
        progressbar.grid(column=0,row=0)
        progressbar.start(10)
        
        print("display progress bar....")
        return prosessing_window

    def create_download_window(self,prosessing_window,event):
        self.wait_for_destorying_open_window(prosessing_window,event)
        download_window = self.create_new_window("処理完了")
        
        mainframe = ttk.Frame(download_window)
        mainframe.grid(column=0, row=0,sticky=(N, W, E, S))
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)

        event = threading.Event()
        request_download_thread  = threading.Thread(target=self.client.tell_server_want_to_download,args=[event])
        
        download_btn = ttk.Button(mainframe, text="Download",command=lambda:[
            download_window.destroy(),
            request_download_thread.start(),
            self.wait_for_destorying_open_window(self.display_progressbar("ダウンロード中"),event),
            self.wait_and_report_to_complete_work("ダウンロードが完了しました。",event)
            ]).grid(column=0, row=0)
   
    def wait_for_destorying_open_window(self, open_window,event):
        event.wait()
        open_window.destroy()
    
    def wait_and_report_to_complete_work(self,message,event):
        event.wait()
        messagebox.showinfo(message=message)

class Main():
    client = Client()
    view_con = ViewController(client)
    view_con.create_main_manu_page()

    
if __name__ == "__main__":
    Main()