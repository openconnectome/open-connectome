Search.setIndex({envversion:46,filenames:["api/data_api","api/functions","api/graphgen_api","api/info_api","api/json_api","api/nifti_api","api/ocp_types","api/overlay_api","api/propagate_api","api/public_api","api/ramon_api","api/swc_api","api/tile_api","index","sphinx/config","sphinx/console","sphinx/faq","sphinx/introduction","sphinx/ocp"],objects:{"":{"(string:host_server_name)/ocp/overlay/(float:alpha_value)/(string:first_server_name)/(string:first_token_name)/(string:first_channel_name)/(string:second_server_name)/(string:second_token_name)/(string:second_channel_name)/xy/(int:resolution)/(int:min_x),(int:max_x)/(int:min_y),(int:max_y)/(int:z_slice)/(int:time_slice)/":[7,1,1,"post-(string-host_server_name)-ocp-overlay-(float-alpha_value)-(string-first_server_name)-(string-first_token_name)-(string-first_channel_name)-(string-second_server_name)-(string-second_token_name)-(string-second_channel_name)-xy-(int-resolution)-(int-min_x),(int-max_x)-(int-min_y),(int-max_y)-(int-z_slice)-(int-time_slice)-"],"(string:host_server_name)/ocp/overlay/(float:alpha_value)/(string:first_server_name)/(string:first_token_name)/(string:first_channel_name)/(string:second_server_name)/(string:second_token_name)/(string:second_channel_name)/xz/(int:resolution)/(int:min_x),(int:max_x)/(int:y_slice)/(int:min_z),(int:max_z)/(int:time_slice/":[7,1,1,"post-(string-host_server_name)-ocp-overlay-(float-alpha_value)-(string-first_server_name)-(string-first_token_name)-(string-first_channel_name)-(string-second_server_name)-(string-second_token_name)-(string-second_channel_name)-xz-(int-resolution)-(int-min_x),(int-max_x)-(int-y_slice)-(int-min_z),(int-max_z)-(int-time_slice-"],"(string:host_server_name)/ocp/overlay/(float:alpha_value)/(string:first_server_name)/(string:first_token_name)/(string:first_channel_name)/(string:second_server_name)/(string:second_token_name)/(string:second_channel_name)/yz/(int:resolution)/(int:x_slice)/(int:min_y),(int:max_y)/(int:min_z),(int:max_z)/(int:time_slice)/":[7,1,1,"post-(string-host_server_name)-ocp-overlay-(float-alpha_value)-(string-first_server_name)-(string-first_token_name)-(string-first_channel_name)-(string-second_server_name)-(string-second_token_name)-(string-second_channel_name)-yz-(int-resolution)-(int-x_slice)-(int-min_y),(int-max_y)-(int-min_z),(int-max_z)-(int-time_slice)-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/(int:annotation_id)/(string:option_args)/(int:resolution)/":[10,0,1,"get-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-(int-annotation_id)-(string-option_args)-(int-resolution)-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/(string:option_args)/":[10,1,1,"post-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-(string-option_args)-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/getField/(string:ramon_field)/":[10,0,1,"get-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-getField-(string-ramon_field)-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/getPropagate/":[11,0,1,"get-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-getPropagate-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/hdf5/(int:resolution)/(int:min_x),(int:max_x)/(int:min_y),(int:max_y)/(int:min_z),(int:max_z)/(int:min_time),(int:max_time)/":[0,1,1,"post-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-hdf5-(int-resolution)-(int-min_x),(int-max_x)-(int-min_y),(int-max_y)-(int-min_z),(int-max_z)-(int-min_time),(int-max_time)-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/npz/(int:resolution)/(int:min_x),(int:max_x)/(int:min_y),(int:max_y)/(int:min_z),(int:max_z)/(int:min_time),(int:max_time)/":[0,1,1,"post-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-npz-(int-resolution)-(int-min_x),(int-max_x)-(int-min_y),(int-max_y)-(int-min_z),(int-max_z)-(int-min_time),(int-max_time)-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/setField/(string:ramon_field)/(string/int/float:ramon_value)":[10,0,1,"get-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-setField-(string-ramon_field)-(string-int-float-ramon_value)"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/setPropagate/(int:propagate_value)/":[8,0,1,"get-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-setPropagate-(int-propagate_value)-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/xy/(int:resolution)/(int:min_x),(int:max_x)/(int:min_y),(int:max_y)/(int:z_slice)/(int:time_slice)/":[0,0,1,"get-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-xy-(int-resolution)-(int-min_x),(int-max_x)-(int-min_y),(int-max_y)-(int-z_slice)-(int-time_slice)-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/xz/(int:resolution)/(int:min_x),(int:max_x)/(int:y_slice)/(int:min_z),(int:max_z)/(int:time_slice/":[0,0,1,"get-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-xz-(int-resolution)-(int-min_x),(int-max_x)-(int-y_slice)-(int-min_z),(int-max_z)-(int-time_slice-"],"(string:server_name)/ocp/ca/(string:token_name)/(string:channel_name)/yz/(int:resolution)/(int:x_slice)/(int:min_y),(int:max_y)/(int:min_z),(int:max_z)/(int:time_slice)/":[0,0,1,"get-(string-server_name)-ocp-ca-(string-token_name)-(string-channel_name)-yz-(int-resolution)-(int-x_slice)-(int-min_y),(int-max_y)-(int-min_z),(int-max_z)-(int-time_slice)-"],"(string:server_name)/ocp/ca/(string:token_name)/createChannel/":[4,1,1,"post-(string-server_name)-ocp-ca-(string-token_name)-createChannel-"],"(string:server_name)/ocp/ca/(string:token_name)/deleteChannel/":[4,1,1,"post-(string-server_name)-ocp-ca-(string-token_name)-deleteChannel-"],"(string:server_name)/ocp/ca/(string:token_name)/info/":[3,0,1,"get-(string-server_name)-ocp-ca-(string-token_name)-info-"],"(string:server_name)/ocp/ca/(string:token_name)/projinfo/":[3,0,1,"get-(string-server_name)-ocp-ca-(string-token_name)-projinfo-"],"(string:server_name)/ocp/ca/createProject/":[4,1,1,"post-(string-server_name)-ocp-ca-createProject-"],"(string:server_name)/ocp/ca/json/":[3,0,1,"get-(string-server_name)-ocp-ca-json-"],"(string:server_name)/ocp/ca/public_tokens/":[9,0,1,"get-(string-server_name)-ocp-ca-public_tokens-"],"(string:server_name)/ocp/catmaid/viking/(string:token_name)/volume/(string:channel_name)/(int:resolution)/X(int:xtile)_Y(int:xtile)_Z(int:zvalue)":[12,0,1,"get-(string-server_name)-ocp-catmaid-viking-(string-token_name)-volume-(string-channel_name)-(int-resolution)-X(int-xtile)_Y(int-xtile)_Z(int-zvalue)"],ocpca:[1,2,0,"-"]},"(string:server_name)/ocp/catmaid/(string:token_name)/(string:channel_name)/(string:slice_type)/(int:time)/(int:zvalue)/(int:ytile)_(int:xtile)_(int:resolution)":{png:[12,0,1,"get-(string-server_name)-ocp-catmaid-(string-token_name)-(string-channel_name)-(string-slice_type)-(int-time)-(int-zvalue)-(int-ytile)_(int-xtile)_(int-resolution).png"]},"(string:server_name)/ocp/catmaid/mcfc/(string:token_name)/(string:channel_name):(string:color_name)/(string:slice_type)/(int:time)/(int:zvalue)/(int:ytile)_(int:xtile)_(int:resolution)":{png:[12,0,1,"get-(string-server_name)-ocp-catmaid-mcfc-(string-token_name)-(string-channel_name)-(string-color_name)-(string-slice_type)-(int-time)-(int-zvalue)-(int-ytile)_(int-xtile)_(int-resolution).png"]}},objnames:{"0":["http","get","HTTP get"],"1":["http","post","HTTP post"],"2":["py","module","Python module"]},objtypes:{"0":"http:get","1":"http:post","2":"py:module"},terms:{"0_0_3":12,"1_1_1":[],"1_1_4":12,"512x512":12,"case":[0,2,3,4,5,7,8,9,10,11,12,15],"default":[0,2,5,7,8,10,11,12,15],"final":15,"float":[6,7,10],"int":[0,7,8,10,12],"new":[15,16,18],"return":6,"true":3,"while":6,about:13,abov:[6,15],access:[9,15],accessor:15,accesss:15,acm:13,across:[6,16,18],activ:[16,18],add:15,adminstr:[],after:15,again:15,algorithm:[13,17],all:[9,13,15,17],allow:[6,15],alpha_valu:7,alreadi:[15,16,18],also:[9,12,15,16],amount:15,analysi:[13,17],anaylsi:0,ani:15,annnot:6,annot:[0,7],annotation_id:10,anoth:15,answer:[16,18],anyon:15,appli:[16,18],applic:[3,4,9,12],appropri:15,architectur:[13,17],archiv:[16,18],argument:10,arrai:[0,13,17],ask:[],aspect:15,associ:[6,15],autom:15,avail:[13,15,17],avali:9,avoid:[13,17],axon:13,background:6,been:15,begin:16,below:[6,15],berger:13,bibtex:13,big:6,bit:[6,15],bock11:[9,15],bock:13,both:6,bound:0,brain:[13,17],branch:[16,18],browser:0,build:[13,17],burn:13,button:15,cajal:15,call:6,can:[0,6,9,10,12,14,15],cannot:[6,15],canon:0,cassandra:14,catmaid:12,celeri:14,center:13,certain:[6,15],chan1:4,chan2:4,chan3:4,chang:15,channel:0,channel_nam:[0,2,4,5,8,10,11,12],channel_typ:4,channeltyp:[0,7],chatroom:13,check:6,checkout:[16,18],chung:13,cite:13,click:15,client:17,clone:[16,18],cluster:[13,17],cmyrgb:12,code:[0,2,3,4,5,7,8,9,10,11,12,16],color:12,color_nam:12,com:13,common:16,commonli:16,comput:[13,17],configur:[],connect:[13,15,17],consist:6,consol:[],contact:1,contain:15,content:[0,3,4,9,12],contribut:[],correspond:10,cortex:13,creat:[4,15],cube_dimens:3,current:15,cut:10,databas:[10,12,13,15,17],dataset:3,datatyp:[0,4,6,7,15],dataurl:3,dbname:3,deisseroth:13,delet:4,dendrit:13,deriv:13,describ:13,descript:15,design:[13,17],desir:15,detail:[10,15],detect:[13,17],dev:[16,18],develop:[16,18],diagram:15,differ:[6,13,17],dimenison:6,dimens:6,direct:[13,15,17],directli:[16,18],disk:[13,17],distribut:[13,17],document:[10,13],doe:6,don:15,done:6,down:15,download:[0,15],downsampl:6,drop:15,dropdown:15,dsp061:3,each:[6,12,15],edit:15,edu:[1,3],effect:[13,17],either:[16,18],electron:[13,17],enabl:15,end:15,engin:15,entit:6,error:[0,2,3,4,5,7,8,9,10,11,12],etc:15,evalu:[13,17],everyon:15,ex10r55:9,ex12r75:9,ex12r76:9,ex13r51:9,ex14r58:9,exampl:[0,3,4,6,9,12,15],except:[3,10,15],execut:[13,17],exist:[4,15],explan:15,extend:[16,18],extens:15,fals:3,faq:[],file:[0,2,3,4,5,7,8,9,10,11,12],fill:15,first:[7,15],first_channel_nam:7,first_server_nam:7,first_token_nam:7,float32:[0,6,7],follow:[15,16,18],form:[0,3,4,7],format:[0,2,3,4,5,7,8,9,10,11,12],formerli:15,forum:[],found:[0,2,3,4,5,7,8,9,10,11,12,15,16,18],frequent:[],from:[0,2,3,5,9,10,11,12,13,15,17],full:15,further:13,gener:[0,2,3,4,5,7,8,9,10,11,12,16],getpropag:[],git:[16,18],github:13,gitter:13,good:15,googlegroup:13,grai:13,graph:[2,5,11],grayscal:12,grosenick:13,group:[0,7],have:[6,13,15],head:[16,18],here:[15,16,18],high:[13,17],highest:15,highlight:[13,17],hold:15,host:[0,3,4,7,9,12,15],host_server_nam:7,how:[15,16],howev:15,http:[0,3,4,9,12],idenitfi:6,images:3,implement:[16,18],improv:[13,17],includ:[13,15,17],index:[13,17],individu:6,inform:[3,9,15,16,18],inherit:[13,17],insid:6,instal:[14,16],integ:6,intens:[13,15,17],interfac:[13,17],interfer:[13,17],introduct:[],isotrop:15,isotropic_slicerang:3,issu:[16,18],jhu:[1,3],kasthuri11:[0,3,9,12],kasthuri:13,kazhdan:13,kei:15,kleissa:13,know:13,kunal:1,kvengin:3,kvserver:3,lastnam:15,learn:16,least:15,left:13,let:[13,15],level:15,librari:0,lichtman:13,lillanei:[1,13],line:15,link:15,list:[4,9,13,16],load:0,localhost:3,locat:15,lock:6,look:[3,4,10],lower:15,lowest:15,mai:[15,16,18],mail:[13,16],main:15,maintain:6,make:[6,15,16,18],manag:15,manavalan:13,mani:15,manipul:15,map:[6,13,17],max_i:[0,7],max_tim:[0,7],max_x:[0,7],max_z:[0,7],maxim:[13,17],maximum:[0,7],mcfc:12,membran:13,mention:6,menu:15,metadata:[3,6],microscopi:[13,17],might:15,min_i:[0,7],min_tim:[0,7],min_x:[0,7],min_z:[0,7],minimum:[0,7],miss:[0,2,5,7,8,10,11,12],modifi:15,more:[10,15],mous:13,much:[13,15,17],mulitpl:6,multi:[13,17],multipl:15,mysql:[3,14],name:[0,2,3,4,5,7,8,9,10,11,12,15],naviagt:16,navig:15,ndio:15,neariso_scaledown:3,need:15,neural:[13,17],neurosci:13,nginx:14,node:[13,17],normal:15,nosql:[13,17],note:13,now:15,npz:0,ocp:[0,3],ocpmatlab:15,ocptilecach:12,ocpviz:16,offset:15,onli:[0,6,7,12,15],openconnecto:[0,2,3,4,5,7,8,9,10,11,12],option:[0,2,5,7,8,10,11,12,15,16,18],option_arg:10,options_arg:10,organ:[13,15,17],other:15,our:[16,18],out:[13,17],output:13,over:[16,18],overal:15,overwrit:10,page:[15,16],paint:6,parallel:[13,17],paramet:[0,2,3,4,5,7,8,9,10,11,12],part:[16,18],particular:15,partit:[13,17],patient:6,peopl:15,perform:[13,17],perlman:13,pha:3,pixel:15,plane:[0,15],pleas:[1,6,13,16],png:12,point:[6,15,16],practic:15,present:15,preserv:10,prevent:15,primarili:[13,17],prior:[16,18],privat:15,probabl:[6,13],probmap:[0,7],product:[13,17],program:[13,17],projecttyp:3,projinfo:3,propag:3,propagate_valu:8,properti:6,propgat:6,provid:[13,16,17],public_token:9,publicli:[9,13,15,17],pull:[16,18],put:9,python:[0,15],question:1,quit:6,rabbitmq:14,ramon:[],ramon_field:10,ramon_valu:10,read:[13,15,17],readonli:[3,4],reduc:15,refer:[6,15,16],reflect:16,region:0,regist:13,reid:13,releas:13,relev:15,repo:[13,16,18],repositori:[16,18],repres:6,request:[0,3,4,9,12,16,18],resolut:[0,3,6,7,10,12,15],respons:[0,3,4,9,12],rest:[13,17],rgb32:[0,7],rgb64:[0,7],rgba:6,riak:14,right:[13,15],righthand:[16,18],roncal:13,run:[16,17],sai:15,same:[6,15],scalabl:[13,17],scale:[13,15,17],schema:3,scienc:[13,17],script:[14,15],search:16,second:7,second_channel_nam:7,second_server_nam:7,second_token_nam:7,see:[15,16,18],select:[15,16,18],seri:[13,15,17],serv:15,server:[0,2,3,4,5,7,8,9,10,11,12,14,15],server_nam:[0,2,3,4,5,8,9,10,11,12],set:[6,8,10,13,14,15,17],share:15,sheet:[3,4],should:[15,16],show:15,side:[16,18],signfi:6,similarli:12,simpl:[13,17],singl:0,size:15,slice_typ:12,slicerang:3,smith:13,solid:[13,17],somatosensori:13,some:[6,16,18],someth:6,spatial:[13,17],spec:16,speci:15,specif:[6,15],specifi:[0,10],ssdbm:13,stack:[13,17],start:[15,16],state:[6,8,13,17],stateless:[13,17],statu:[0,2,3,4,5,6,7,8,9,10,11,12,15],step:15,storag:[13,17],store:[6,13,15],string:[0,2,3,4,5,7,8,9,10,11,12],sub:15,success:[3,4],suggest:[16,18],support:[],synaps:17,synopsi:[0,2,3,4,5,7,8,9,10,11,12],syntax:[0,2,3,4,5,7,8,9,10,11,12],system:[13,17],szalai:13,tabl:6,take:6,takemura13:9,tamper:15,tar:13,tech:[3,4],templat:15,test_kat1:4,thei:15,them:15,themselv:15,thi:[0,2,3,4,5,6,7,8,9,10,11,12,15,16,18],thing:15,through:15,throughput:[13,17],thy1eyfpbrain10:12,tiff:0,tilecach:12,time:[6,12,13,15,16,17],time_slic:[0,7],timerang:[0,3,7],timeseri:[0,6,7,12,15],timseri:6,todo:14,token:[0,3,7,8],token_nam:[0,2,3,4,5,8,10,11,12],touch:[16,18],turn:15,two:15,type:[0,3],ualex:14,uint16:[0,6,7],uint32:[0,6,7],uint64:6,uint8:[0,4,6,7],under:[6,16,18],unintention:15,uniqu:6,updat:[15,16],upsampl:6,usabl:[13,17],user:[15,16],usual:15,valu:[0,6,7,10,12,15],variou:15,version:3,via:[6,15],view:[12,15,16],viewabl:15,vike:12,vision:[13,17],visit:16,visual:17,vogelstein:13,volum:12,voxel:15,wai:15,want:15,warn:6,web:[13,16,17],weiler:13,well:15,what:[15,16],when:[6,15],where:15,whether:15,which:[6,12,13,15,16,17],who:15,window:15,windowrang:3,wish:[15,16],within:15,work:12,workflow:17,workload:[13,17],would:15,write:[13,15,17],x1_y1_z10:12,x_slice:[0,7],xrang:[0,7],xtile:12,xyz:6,y_slice:[0,7],year:15,yet:15,you:[0,6,12,13,14,15,16],your:[0,6,15,16,18],yrang:[0,7],ytile:12,z_slice:[0,7],zenodo:13,zip:13,zrang:[0,7],zscale:3,zslice:12,zvalu:12},titles:["Data API&#8217;s","open-connectome Functions","GrahpGen API&#8217;s","Project Info API&#8217;s","JSON API&#8217;s","NIFTI API&#8217;s","OCP Types","Overlay API&#8217;s","Propagate API&#8217;s","Public Token API&#8217;s","RAMON API&#8217;s","SWC API&#8217;s","Tile API&#8217;s","Open Connectome","Configuration","Adminstrator Console","Frequently Asked Questions (FAQ)","Introduction","OCP"],titleterms:{"function":1,"public":9,adminstr:15,annot:[10,15],api:[0,2,3,4,5,7,8,9,10,11,12],ask:16,channel:[6,15],combin:6,configur:14,connectom:1,consol:15,contact:13,contribut:18,createchannel:4,createproject:4,creation:15,cutout:[0,7],cutut:7,data:[0,6],dataset:15,deletechannel:4,faq:16,field:10,forum:18,frequent:16,get:[0,3,7,9,10],getfield:10,getgraph:2,getmcfctil:12,getnifti:5,getpropag:8,getsimpletil:12,getswc:11,getvikingtil:12,grahpgen:2,hdf5:[0,3],imag:[0,15],info:3,introduct:17,json:[3,4],merg:10,nifti:5,numpi:0,object:10,ocp:[6,13,18],open:1,overlai:7,overview:15,possibl:6,post:[0,3,10],project:[3,15],propag:[6,8],queri:10,question:16,quickstart:15,ramon:10,servic:[0,3,6,7,10],setfield:10,setpropag:8,slice:[0,7],support:18,swc:11,tile:12,token:[9,15],tutori:15,type:6,upload:15}})