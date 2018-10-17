import sqlite3

from  selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import urllib3
from lxml import etree
import re
import json

class JobsSpider(object):

	def crawl(self,root_url,keyword):


		driverChrom=webdriver.Chrome()
		driverChrom.get(root_url)
		try:
			element=WebDriverWait(driverChrom,10).until(EC.presence_of_element_located((By.ID,"kwdselectid")))
		except Exception as E:
			print(E)
		driverChrom.maximize_window()
		element_key=driverChrom.find_element_by_id("kwdselectid")
		element_search=driverChrom.find_element_by_xpath("/html/body/div[3]/div/div[1]/div/button")
		element_key.send_keys(keyword)
		time.sleep(3)
		element_search.click()
		time.sleep(3)

		resultUrl=driverChrom.current_url

		self.GetResultPageList(resultUrl, keyword)

	def GetResultPageList(self,resultUrl, keyword):
		http=urllib3.PoolManager()
		request=http.request('GET',resultUrl)
		# 获取总页数
		html = etree.HTML(request.data)
		lastPages = html.xpath("//div[@class='p_in']/span[@class='td'][1]/text()")
		numStr = str(lastPages)
		# print(lastPages)
		lastPageNum = re.findall("\d+", numStr)[0]
		# print(int(lastPageNum)+1)

		# 拼接所有页面链接
		allPageUrl = []
		for i in range(1, int(lastPageNum) + 1):

			# pages = "https://search.51job.com/list/030200,000000,0000,00,9,99,"++",2," + str(
			# 	i) + ".html?lang=c&stype=1&postchannel=0000&workyear=99&cotype=99&degreefrom=99&jobterm=99&companysize=99&lonlat=0%2C0&radius=-1&ord_field=0&confirmdate=9&fromType=4&dibiaoid=0&address=&line=&specialarea=00&from=&welfare"
			pages=re.sub("(\d+).html",str(i)+'.html', resultUrl)#这里直接替换了第一个结果页里面的页数（如果采用拼接方式，需要拼接搜索关键词的url编码（2次）以及页数，所以这里采取直接匹配页数直接替换的方式）
			# print(pages)
			allPageUrl.append(pages)

		self.GetJobsUrls(allPageUrl, keyword)

	def GetJobsUrls(self,allPageUrl, keyword):
		# print(allPageUrl)
		allJobsUrl = []
		for i in allPageUrl:
			print(i)
			http = urllib3.PoolManager()
			request = http.request('GET', i)
			html = etree.HTML(request.data)
			jobUrl = html.xpath("//div[@id='resultList']/div[@class='el']/p[@class='t1 ']/span/a/@href")
			time.sleep(0.5)
			for j in jobUrl:
				allJobsUrl.append(j)

		# print(len(allJobsUrl))
		self.GetJobsDetails(allJobsUrl, keyword)


	def SearchJobID(self):
		conn = sqlite3.connect("F:\learning\\test.db")
		cur = conn.cursor()

		create_tb = "CREATE TABLE Jobs_test4(DBID INTEGER PRIMARY KEY   AUTOINCREMENT,ID VARCHAR (20) NOT NULL, DATASOURCE VARCHAR(20),KEYWORD VARCHAR (20),JOBID VARCHAR (20) NOT NULL,JOBNAME VARCHAR(80), JOBSALARY VARCHAR(30),AREA VARCHAR(30), EXPERIENCE VARCHAR (30),  EDUCATION VARCHAR (30), PULISHDTE VARCHAR (20), OTHERCONDITION_1 VARCHAR (20), OTHERCONDITION_2 VARCHAR (20), OTHERCONDITION_3 VARCHAR (20), OTHERCONDITION_4 VARCHAR (20),JOBINFO VARCHAR(4000), COMPANYNAME VARCHAR (80), COMPANYPROPERY VARCHAR (20), COMPANYSCALE VARCHAR (20),COMPANYINDUSTRY VARCHAR (50));"

		# cur.execute(create_tb)

		sql_search = "select id from Jobs_test4 "  # 用jobID去数据库查询

		cur.execute(sql_search)
		result=cur.fetchall()
		db_data=set()
		for i in result:
			for j in i:
				db_data.add(j)
		# print(db_data)
		return db_data


	def GetJobsDetails(self,allJobsUrl, keyword):

		# conn = sqlite3.connect("F:\learning\\test.db")
		# cur = conn.cursor()
		#获取数据库中职位id
		db_data=self.SearchJobID()
		print(db_data)

		allJobs = {}
		details = {}
		id = 1
		joburl_list=[]
		jobid_list_other=[]
		spider_job_id = set()
		for i in allJobsUrl:
			print(i)
			print("="*32)

			url_id = re.findall("https://jobs.51job.com/.*?/(\d+).html\?s=.*?&t=.*?", i)#首先匹配一下详细页的ID，这里是一个包含多个数字的list，而jobid在第二个数
			# print(url_id)
			if len(url_id)!=0:
				job_id_detail=url_id[0]
			# if job_id_detail!="":#这里不能直接判断url_id[1]会报错。所以判断该list长度是否大于1（因为爬虫可能会碰到其他不符合要求的地址，所以要做这个判断）
				# job_id = url_id[0]

				# print(job_id_detail)
				# 将爬取的符合51job详情页的id放入集合
				spider_job_id.add(job_id_detail)
				# 将爬取的符合51job详情页的链接放到列表
				joburl_list.append(i)
			else:
				#这里是不符合标准的url
				jobid_list_other.append(i)
			# print(spider_job_id)
		print("不符合的详情ULR："+str(len(jobid_list_other)))
		#求爬取的标准URL的id和数据库中id的差集。获取新的id
		new_job_id=spider_job_id-db_data
		print(new_job_id)
		print("新增详情页URL："+str(len(new_job_id)))



		AdetailUrl = joburl_list[0]
		for i in new_job_id:
			# 使用新爬到的id拼接详情页链接
			print(i)
			job_detail_url=re.sub("(\d+).html",str(i)+'.html', AdetailUrl)
			print(job_detail_url)

				# print(job_id)

				# sql_search = "select jobid from Jobs_test2 "#用jobID去数据库查询
				# cur.execute(sql_search)
				# result = cur.fetchall()

				# print(result)

				# if result==None:#数据库中不存在该jobid再进一步操作
				# 	jobid_list.append(i)
				#
			#爬取链接
			http = urllib3.PoolManager()
			request = http.request('GET', job_detail_url)

			html = etree.HTML(request.data)
			time.sleep(0.5)

			jobName = html.xpath(".//div[@class='cn']/h1/@title")
			jobName = "".join(jobName)
			jobSalary = html.xpath(".//div[@class='cn']/strong/text()")
			jobSalary = "".join(jobSalary)
			jobAbstract = html.xpath(".//p[@class='msg ltype']/@title")
			jobAbstract = "".join(jobAbstract)
			jobAbstract = jobAbstract.split()
			# jobAbstractInfo = []
			# if(len(jobAbstractInfo)>0):
			# 	for i in range(0, len(jobAbstract), 2):
			# 		# print()
			# 		jobAbstractInfo.append(jobAbstract[i])
			jobInfo = html.xpath(".//div[@class='tBorderTop_box'][1]/div[@class='bmsg job_msg inbox']/p/span/span/text()")
			if len(jobInfo)==0:
				jobInfo = html.xpath(".//div[@class='tBorderTop_box'][1]/div[@class='bmsg job_msg inbox']/p/text()")
			jobInfo = "".join(jobInfo)
			companyName = html.xpath(".//a[@class='com_name ']/p/@title")
			if len(companyName)==0:
				companyName = html.xpath(".//a[@class='com_name himg']/p/@title")
			companyName = "".join(companyName)
			companyProperty = html.xpath(".//div[@class='com_tag']/p[@class='at'][1]/@title")
			companyProperty = "".join(companyProperty)
			companyScale = html.xpath(".//div[@class='com_tag']/p[@class='at'][2]/@title")
			companyScale = "".join(companyScale)
			companyIndustry = html.xpath(".//div[@class='com_tag']/p[@class='at'][3]/@title")
			companyIndustry = "".join(companyIndustry)

			dictInfo = {}
			dictInfo['KeyWord'] = keyword
			dictInfo['JobID']=id
			dictInfo['jobName']=jobName
			dictInfo['jobSalary']=jobSalary
			dictInfo['jobAbstract']=jobAbstract
			# dictInfo['area'] = jobAbstractInfo[0]
			# dictInfo['experience'] = jobAbstractInfo[1]
			# dictInfo['education'] = jobAbstractInfo[2]
			dictInfo['jobInfo']=jobInfo
			dictInfo['companyName']=companyName
			dictInfo['companyProperty']=companyProperty
			dictInfo['companyScale']=companyScale
			dictInfo['companyIndustry']=companyIndustry

			details['JobDetails']=dictInfo

			key = str(i)

			eachJob={
				key:dictInfo
			}

			allJobs.update(eachJob)

			id=id+1

			# else: #jobID存在则跳过
			# 	print("url is exist Pass!!!")
		# else:
		# 	jobid_list_other.append(i)
		# 	len(jobid_list_other)

			# time.sleep(0.5)
	# print(jobid_list)
	# print(jobid_list_other)
	#
	# print(len(jobid_list))
	# print(len(jobid_list_other))
		self.DataStore(allJobs, keyword)

	def DataStore(self,allJobs, keyword):

		jsonString=json.dumps(allJobs,ensure_ascii=False)

		time_now = time.strftime("%Y%m%d_%H%M%S", time.localtime())
		print(time_now)

		with open(keyword+'_jobs_'+time_now+'.json','w',encoding='utf-8') as jsonFile:
			jsonFile.write(jsonString)



if __name__=="__main__":
	keyworks_list = [ '前端', 'python','大数据', 'java']
	spider = JobsSpider()
	for i in keyworks_list:
		spider.crawl("https://www.51job.com/", i)