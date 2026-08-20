import os
import argparse
import logging
import time
import hashlib
from pathlib import Path
from urllib.parse import urlparse
from pytubefix import Playlist
from pytubefix import YouTube
from pytubefix import helpers
from pytubefix import request
logger=logging.getLogger(__name__)
#Prerequisites
class _Format:
    statusTask={}
    @classmethod
    def Stat(cls,status:int,message:str,prompt:str=None,question:str=None,*,taskid:str=False):
        statDataList=[
            {'key':'-','ansiSym':f"\033[91m(-)\033[0m"},
            {'key':'+','ansiSym':f"\033[92m(+)\033[0m"},
            {'key':'*','ansiSym':f"\033[93m(*)\033[0m"},
            {'key':'!','ansiSym':f"\033[6;91m(!)\033[0m"},
            {'key':'?','ansiSym':f"\033[5;94m(?)\033[0m"}
        ]
        statData=statDataList[status]
        formattedStatus=(
            f"{statData['ansiSym']} {message}"
            f"{f"\n\033[1;37m{question}\033[0m" if question else ''}"
            f"{f"\n{prompt}" if prompt else ''}"
        )
        if taskid:
            prevLen=len(cls.statusTask)
            cls.statusTask[taskid]=formattedStatus
            jumpStr=f"\033[{prevLen}F\033[J" if prevLen>0 else ""
            outputMessage=f"{jumpStr}{str.join('\n',cls.statusTask.values())}"
            return outputMessage
        else:
            cls.statusTask={}
            return formattedStatus
    @classmethod
    def Help(cls,helpstring:str,default:str=None,choices:str=None):
        ansiNorm="\033[0;34m"
        ansiBold="\033[1;95m"
        extraInfo=f"\t{ansiNorm}({str.join(f"{ansiNorm}, ",filter(None,[(f'Choices: {ansiBold}'+choices if choices else choices),(f'Default={ansiBold}'+default if default else default)]))}{ansiNorm})" if (choices or default) else ""
        return helpstring+extraInfo
def _create_directory(path):
    try:
        #print('fake')
        os.makedirs(path)
    except OSError as e:
        print(_Format.Stat(0,f"Error while creating directory '{path}'."))
        exit(0)
    print(_Format.Stat(1,f"Directory '{path}' created successfully."))
#Variables
global ARGS
global FORCE
global FILETYPE
global YTURL
global PLAYLIST
global OUTPUT_DIRECTORY
global PROXY
global FILELIST
#Parameters
_parser = argparse.ArgumentParser(
    prog='Download Playlist (Windows)',
    description='Uses PyTubeFix to download a given unlisted or public playlist in a given format.',
    epilog='Notice: Please run \'pip install pytubefix\' if pytubefix is not installed.'
)
#   Arguments
_parser.add_argument(
    "Url",#"-u", "-Url", "--url",
    type = str,
    metavar = "YtUrl",
    help = _Format.Help("Youtube playlist URL.")
)
_parser.add_argument(
    "-o", "--OutputDirectory", "--outputdirectory",
    type = Path,
    default = f"~/Downloads/?\uE000",
    metavar = "DIR",
    help = _Format.Help("Path to the output directory.","'$HOME/Downloads/{PlaylistName}'")
)
_parser.add_argument(
    "-t", "--FileType", "--filetype",
    type = str,
    default = "m4a",
    choices=["video/webm", "video/mp4", "audio/mp4", "audio/m4a"],
    metavar = "FILETYPE",
    help = _Format.Help("File format of playlist video.","'audio/m4a'",'{mp3, mp4, m4a}')
)
_parser.add_argument(
    "-p", "--Proxy", "--proxy",
    type = str,
    default = None,
    metavar = "PROXY",
    help = _Format.Help("Proxy address.","'None'")
)
#   Flags (Could add --keepplaylistname to use yt playlist name for given output directory, perhaps later.)
_parser.add_argument(
    "-r", "--Replace", "--replace",
    default=False,
    action="store_true",
    help=_Format.Help("Enable flag to replace existing files with same name.")
)
_parser.add_argument(
    "-f", "--Force", "--force",
    default=False,
    action="store_true",
    help=_Format.Help("Enable flag to force script to accept output directory/create playlist folder automatically.")
)
class _ParamEval:
    #Argument definition
    ARGS = _parser.parse_args()
    def __init__(self,parser):
        global ARGS
        ARGS = self.ARGS
    #FORCE
    @classmethod
    def _force(cls):
        global FORCE
        FORCE = cls.ARGS.Force
    #FILETYPE
    @classmethod
    def _filetype(cls):
        global FILETYPE
        FILETYPE = cls.ARGS.FileType
    #YTURL
    @classmethod
    def _yturl(cls):
        global YTURL
        YTURL=cls.ARGS.Url
        assert "youtube.com" in urlparse(YTURL).netloc
    #PLAYLIST
    @classmethod
    def _playlist(cls):
        global PLAYLIST
        PLAYLIST=Playlist(YTURL)
    #PROXY
    @classmethod
    def _proxy(cls):
        #Variables
        global PROXY
        global FORCE
        #Execute
        #   If a proxy is supplied by user
        if cls.ARGS.Proxy==True and not FORCE:
            _input = input(_Format.Stat(4, f"Notice: You have not specified a proxy, would you like to add one?", "(<IpAddr>ProxyAddr/<None>Continue) > ","You may want to consider adding a proxy to avoid potential Youtube ip blocking (Ex. 192.168.0.1)."))
            if _input:
                cls.ARGS.Proxy=_input
        #   If the proxy argument exists (default or supplied)
        if cls.ARGS.Proxy:
            PROXY = {
                "http": f"socks5://{cls.ARGS.Proxy}",
                "https": f"socks5://{cls.ARGS.Proxy}"
            }
            #   FIX VALIDATION LATER! (Given the circumstances I need this program up and running, don't have the time to deal with this)
            '''
            helpers.install_proxy(PROXY)
            print(request.urlopen(request.Request("https://ifconfig.io/",headers={"User-Agent": "Mozilla/5.0"})))
            '''
    #OUTPUT_DIRECTORY
    @classmethod
    def _outputDirectory(cls):
        #Variables
        global OUTPUT_DIRECTORY
        global FORCE
        OUTPUT_DIRECTORY = cls.ARGS.OutputDirectory.expanduser().resolve()
        _PARENT_DIRECTORY = lambda : Path(str(OUTPUT_DIRECTORY)+'/..').expanduser().resolve() #its an expression
        #Logic functions
        OutputPathIsFolder=lambda:OUTPUT_DIRECTORY==Path("~/Downloads").expanduser().resolve()
        OutputPathNotExist=lambda:not OUTPUT_DIRECTORY.exists()
        OutputParamIsDefault=lambda:FORCE or (OUTPUT_DIRECTORY==Path("~/Downloads/?\uE000").expanduser().resolve())
        OutputPathParentIsUser=lambda:_PARENT_DIRECTORY()==Path("~").expanduser().resolve() and not FORCE
        #Execute
        if OutputPathIsFolder:
            OUTPUT_DIRECTORY = Path(str(OUTPUT_DIRECTORY) + "/" + PLAYLIST.title)
            _create_directory(OUTPUT_DIRECTORY)
        if OutputPathNotExist:
            if OutputParamIsDefault:
                try:
                    OUTPUT_DIRECTORY = Path(str(OUTPUT_DIRECTORY)[0:-2] + "/" + PLAYLIST.title)
                    _create_directory(OUTPUT_DIRECTORY)
                except Exception as e:
                    logging.error(e)
                    print(_Format.Stat(0,f"Warning, default directory '{OUTPUT_DIRECTORY}' does not exist, please specify an output directory with '-o <PATH>'."))
                    exit(1)
            #   Output path doesnt exist.
            else:
                _input=input(_Format.Stat(3,f"Directory '{OUTPUT_DIRECTORY}' does not exist, would you like to create it?", "(y/n) > "))
                #   User has chosen to create non-existing output directory.
                if _input and _input.lower()[0] == "y":
                    _create_directory(OUTPUT_DIRECTORY)
                #   User has not specified an existing output directory, exit program.
                else:
                    exit(1)
        #   Validate existence of output path, and if it's a folder.
        else:
            global FILELIST
            #   OsError if Path doesnt exist
            os.path.realpath(OUTPUT_DIRECTORY,strict=True)
            #   OsError if Path is not a directory
            FILELIST=os.listdir(OUTPUT_DIRECTORY)
        #   Prevent accidental output into an unwanted directory, like downloads.
        if OutputPathParentIsUser:
            _input = input(_Format.Stat(3,f"Output directory '{OUTPUT_DIRECTORY}' Parent is UserFolder, did you intend to output playlist into UserFolder?","(y/<string>PlaylistName/<None>Cancel) > ", "Please specify a playlist folder name ('y' to keep output directory, leave blank to cancel)."))
            #   User has specified a playlist name
            if _input and _input.lower()[0] != "y":
                OUTPUT_DIRECTORY=Path(str(OUTPUT_DIRECTORY)+"/"+_input)
                _create_directory(OUTPUT_DIRECTORY)
                #   Note: If user navigates to a non-existent path, only an error exception will be able to stop the program
            #   User has chosen to cancel program, input is <Empty>
            elif not _input:
                exit(1)
            #   User has chosen option 'y', (sorry about the poor decision block organization)
    @classmethod
    def paramInterpret(cls,*,_nUseExit=0):
        #   Prevent function looping risk entirely
        if _nUseExit==1: return 0
        #   Execute all non-class functions except for this function
        for key in dir(cls):
            funcVal=cls.__getattribute__(cls,key)
            if key.startswith("__") and callable(funcVal) and key!='paramInterpret':
                logger.info(f"Param init, '{key}' function started")
                funcVal(_nUseExit=1)
                logger.info(f"Param init, '{key}' function complete")
        return 1
#Functions
def download_playlist(playlist):
    #Functions
    def _download(video_url):
        #Prerequisites
        prevTime=time.time()
        taskId=(#   Hashed for privacy
            hashlib.blake2b(video_url[32:].encode(), digest_size=4).hexdigest())
        logger.info(f"Download '{taskId}' started")
        print(_Format.Stat(2,f"{taskId} task created (...)s",taskid=taskId))
        #Macros
        def check_proxy():
            return YouTube(video_url,'WEB_MUSIC',proxies=PROXY) if PROXY else YouTube(video_url,'WEB_MUSIC')
        #Variables
        yt=check_proxy()
        title:str=yt.title.title()
        streams=yt.streams
        videoStream=[]
        #Functions
        def on_progress(stream2, chunk, bytes_remaining):
            total = stream2.filesize
            percent = (1 - bytes_remaining / total) * 100
            print(_Format.Stat(2, f"'{title}' Pending [{percent:.2f}%]", taskid=taskId))
        #Execute
        #   Loading progress
        print(_Format.Stat(2, f"'{title}' Pending [...]", taskid=taskId))
        yt.register_on_progress_callback(on_progress)
        #   Check file format and apply stream filter, assign to videoStream
        if FILETYPE=="video/webm":
            videoStream=streams.filter(file_extension="webm", only_video=True).first()  #.download()
        elif FILETYPE=="video/mp4":
            videoStream=streams.filter(file_extension="mp4", only_video=True).first()
        elif FILETYPE=="audio/mp4":
            videoStream=streams.filter(file_extension="mp4", only_audio=True).first()
        elif FILETYPE=="audio/m4a":
            videoStream=streams.filter(only_audio=True).get_audio_only()
        #   Download video
        videoStream.download(OUTPUT_DIRECTORY, skip_existing=(False if ARGS.Replace else True))
        #PostExecution
        #   Log benchmark time
        finalTime=(time.time()-prevTime)
        print(_Format.Stat(1,f"'{title}' Completed ({finalTime:.2f})s",taskid=taskId))
        logger.info(f"Download '{taskId}' completed with time ({finalTime:.2f})s")
    #Execute
    logger.info('Compiling download tasks')
    #   Download all videos in playlist
    for _video_url in PLAYLIST.video_urls:
        _download(_video_url)
    logger.info('Awaiting download tasks')
def Main():
    #Prerequisites
    logging.basicConfig(filename='downloadpy.log', level=logging.INFO)
    logger.info('Begin (*)')
    prevTime=time.time()
    #Execute
    #   Download playlist main function
    download_playlist(PLAYLIST)
    #PostExecution
    #   Log benchmark time
    finalTime=(time.time()-prevTime)
    print(_Format.Stat(1,f"Playlist downloaded in {finalTime:.2f}s."))
    logger.info('End (-)')
#Execute
if __name__ == '__main___':
    _ParamEval.paramInterpret()
    Main()