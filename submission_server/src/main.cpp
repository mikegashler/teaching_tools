// -------------------------------------------------------------
// The contents of this file may be distributed under the CC0
// license (http://creativecommons.org/publicdomain/zero/1.0/).
// -------------------------------------------------------------

#include <stdio.h>
#include <stdlib.h>
#ifdef WINDOWS
#	include <windows.h>
#	include <process.h>
#	include <direct.h>
#else
#	include <unistd.h>
#endif
#include <GClasses/GDynamicPage.h>
#include <GClasses/GImage.h>
#include <GClasses/GDirList.h>
#include <GClasses/GHolders.h>
#include <GClasses/GApp.h>
#include <GClasses/GDom.h>
#include <GClasses/GString.h>
#include <GClasses/GHeap.h>
#include <GClasses/GHttp.h>
#include <GClasses/GFile.h>
#include <GClasses/GTime.h>
#include <GClasses/GRand.h>
#include <GClasses/GHashTable.h>
#include <GClasses/GTokenizer.h>
#include <GClasses/sha1.h>
#include <sys/wait.h>
#include <wchar.h>
#include <string>
#include <vector>
#include <exception>
#include <iostream>
#include <sstream>
#include <cmath>

using namespace GClasses;
using std::cout;
using std::cerr;
using std::vector;
using std::string;
using std::ostream;
using std::map;


class View;
class Account;
class ViewJob;

class Connection : public GDynamicPageConnection
{
public:
	Connection(SOCKET sock, GDynamicPageServer* pServer) : GDynamicPageConnection(sock, pServer)
	{
	}
	
	virtual ~Connection()
	{
	}

	virtual void handleRequest(GDynamicPageSession* pSession, std::ostream& response);
};


class Server : public GDynamicPageServer
{
public:
	std::string m_basePath;
	vector<ViewJob*> m_jobs;

	// Typically the accounts would be stored in a database, but since this is
	// just a demo, we'll keep them all in memory for simplicity.
	std::map<std::string,Account*> m_accounts;

public:
	Server(int port, GRand* pRand);
	virtual ~Server();
	void addJob(ViewJob* pJob);
	void nukeJob(ViewJob* pJob);
	size_t jobCount() { return m_jobs.size(); }
	virtual void onEverySixHours();
	virtual void onStateChange();
	virtual void onShutDown();
	void makePage(const char* szUrl, GDynamicPageSession* pSession, ostream& response);

	virtual GDynamicPageConnection* makeConnection(SOCKET sock)
	{
		return new Connection(sock, this);
	}
};

class View
{
protected:
	Server* m_pServer;

public:
	View(Server* pServer) : m_pServer(pServer) {}
	virtual ~View() {}

	virtual void makePage(const char* szUrl, GDynamicPageSession* pSession, ostream& response) = 0;
};

// ------------------------------------------------------

string scrub_string(string& s)
{
	size_t alphanum = 0;
	string s2 = s;
	for(size_t i = 0; i < s2.length(); i++)
	{
		if(	(s2[i] >= 'a' && s2[i] <= 'z') ||
			(s2[i] >= 'A' && s2[i] <= 'Z') ||
			(s2[i] >= '0' && s2[i] <= '9'))
		{
			alphanum++;
		}
		else if(s2[i] == '.')
		{
		}
		else
			s2[i] = '_';
	}
	if(alphanum > 0)
		return s2;
	else
		return "empty";
}

class ViewJob : public View
{
protected:
	time_t m_time;
	string m_jobname;
	GPipe m_pipeOut;
	GPipe m_pipeErr;
	int m_pid;
	size_t m_projectNumber;
	string m_meta;
	string m_s;
	size_t m_counter;
	GDom* m_pDoc;

public:
	ViewJob(string& jobname, string& batchname, size_t projectNumber, string& meta, string& s, Server* pServer, GDom* pDoc) : View(pServer), m_jobname(jobname), m_projectNumber(projectNumber), m_meta(meta), m_s(s), m_counter(0), m_pDoc(pDoc)
	{
		// Launch the job
		time(&m_time);
		m_pid = GApp::systemExecute(batchname.c_str(), false, &m_pipeOut, &m_pipeErr, NULL);
	}

	virtual ~ViewJob()
	{
		delete(m_pDoc);
	}

	string& jobName() { return m_jobname; }

	time_t timeStamp() { return m_time; }

	void checkResults(size_t proj, string& meta, string& sOutput, string& sErr, string& sPath, ostream& response)
	{
		// Find the project rules
		GDomNode* pProj = NULL;
		const GDomNode* pNode = m_pDoc->root();
		GDomListIterator it(pNode);
		size_t index = 1;
		while(it.remaining() > 0)
		{
			if(proj == index)
			{
				pProj = it.current();
				break;
			}
			index++;
			it.advance();
		}
		if(pProj == NULL)
			throw Ex("No such project: ", to_str(proj));

		// Apply each rule
		const char* szOutput = sOutput.c_str();
		const char* szErr = sErr.c_str();
		bool passfail = false;
		bool noscore = false;
		ssize_t score = 0;
		ssize_t score_floor = 0;
		ssize_t score_cap = 100;
		GDomListIterator it2(pProj->field("rules"));
		while(it2.remaining() > 0)
		{
			GDomNode* pRule = it2.current();
			const char* szType = pRule->field("type")->asString();
			if(strcmp(szType, "passfail") == 0) // Specify that any scores < 100 are set to 0
			{
				passfail = true;
				GDomNode* pMess = pRule->fieldIfExists("message");
				if(pMess)
				{
					const char* szText = pMess->asString();
					meta += szText;
					meta += ",";
				}
			}
			else if(strcmp(szType, "noscore") == 0) // Specify to not report a score at the end
			{
				noscore = true;
				GDomNode* pMess = pRule->fieldIfExists("message");
				if(pMess)
				{
					const char* szText = pMess->asString();
					meta += szText;
					meta += ",";
				}
			}
			else if(strcmp(szType, "find") == 0) // Add or subtract points if a certain string is found in stdout
			{
				const char* szNeedle = pRule->field("name")->asString();
				const char* szInst = strstr(szOutput, szNeedle);
				int points = (int)pRule->field("points")->asInt();
				if(szInst)
				{
					score += points;
					meta += "Found \"";
					meta += szNeedle;
					meta += "\" in the output. (";
					meta += to_str(points);
					if(points >= 0)
					{
						meta += "/";
						meta += to_str(points);
					}
					meta += "),";
				}
				else
				{
					if(points >= 0)
					{
						meta += "Did not find \"";
						meta += szNeedle;
						meta += "\" in the output. (0/";
						meta += to_str(points);
						meta += "),";
					}
				}
			}
			else if(strcmp(szType, "finderr") == 0) // Add or subtract points if a certain string is found in stderr
			{
				const char* szNeedle = pRule->field("name")->asString();
				const char* szInst = strstr(szErr, szNeedle);
				int points = (int)pRule->field("points")->asInt();
				if(szInst)
				{
					score += points;
					meta += "Found \"";
					meta += szNeedle;
					meta += "\" in stderr. (";
					meta += to_str(points);
					if(points >= 0)
					{
						meta += "/";
						meta += to_str(points);
					}
					meta += "),";
				}
				else
				{
					if(points >= 0)
					{
						meta += "Did not find \"";
						meta += szNeedle;
						meta += "\" in stderr. (0/";
						meta += to_str(points);
						meta += "),";
					}
				}
			}
			else if(strcmp(szType, "value") == 0) // Test whether a reported value is within a specified range
			{
				const char* szNeedle = pRule->field("name")->asString();
				const char* szInst = strstr(szOutput, szNeedle);
				double valMin = pRule->field("min")->asDouble();
				double valMax = pRule->field("max")->asDouble();
				int points = (int)pRule->field("points")->asInt();
				if(szInst)
				{
					// Trim whitespace and copy the value into a buffer
					char buf[256];
					const char* szVal = szInst + strlen(szNeedle);
					while(*szVal <= ' ' && *szVal != '\0')
						szVal++;
					char* pBuf = buf;
					while(*szVal > ' ')
					{
						*pBuf = *szVal;
						pBuf++;
						szVal++;
					}
					*pBuf = '\0';

					// Convert to a double value
					double val = atof(buf);

					meta += szNeedle;
					meta += buf;
					meta += ": ";
					if(val >= valMin && val <= valMax)
					{
						score += points;
						if(passfail)
							meta += "(Requirement satisfied)\n";
						else
						{
							meta += "(";
							meta += to_str(points);
							meta += "/";
							meta += to_str(points);
							meta += "),";
						}
					}
					else
					{
						meta += "Value not within the expected range";
						/*meta += ", [";
						meta += to_str(valMin);
						meta += ",";
						meta += to_str(valMax);
						meta += "]";*/
						meta += ".";
						if(passfail)
						{
							meta += "(Requirement not satisfied)\n";
						}
						else
						{
							meta += "(0/";
							meta += to_str(points);
							meta += "),";
						}
					}
				}
				else
				{
					meta += "Did not find the exact string \"";
					meta += szNeedle;
					meta += "\" in the output. (0/";
					meta += to_str(points);
					meta += "),";
				}
			}
			else if(strcmp(szType, "add") == 0) // Just give some free points
			{
				int points = (int)pRule->field("points")->asInt();
				score += points;
			}
			else if(strcmp(szType, "countlines") == 0) // Count the number of lines between two strings. Give points if the count is within a specified range.
			{
				GDomNode* pFrom = pRule->fieldIfExists("from");
				GDomNode* pTo = pRule->fieldIfExists("to");
				size_t valMin = pRule->field("min")->asInt();
				size_t valMax = pRule->field("max")->asInt();
				int points = (int)pRule->field("points")->asInt();
				const char* szStart = pFrom ? strstr(szOutput, pFrom->asString()) : szOutput;
				if(szStart)
				{
					const char* szEnd = pTo ? strstr(szStart, pTo->asString()) : szStart + strlen(szStart);
					if(szEnd)
					{
						size_t count = 0;
						while(szStart < szEnd)
						{
							if(*szStart == '\n')
								count++;
							szStart++;
						}
						if(count >= valMin && count <= valMax)
						{
							score += points;
							meta += "Found the expected number of lines. (";
							meta += to_str(points);
							meta += "/";
							meta += to_str(points);
							meta += "),";
						}
						else
						{
							meta += "Expected ";
							meta += to_str(valMin);
							meta += " to ";
							meta += to_str(valMax);
							meta += " lines of output here. Found ";
							meta += to_str(count);
							meta += ".,";
						}
					}
					else
					{
						meta += "Did not find the expected string, \"";
						meta += pTo->asString();
						meta += "\".,";
					}
				}
				else
				{
					meta += "Did not find the expected string, \"";
					meta += pFrom->asString();
					meta += "\".,";
				}
			}
			else
			{
				meta += "Autograder error: Unrecognized rule, ";
				meta += szType;
				meta += ". You should probably yell at the instructor about this.,";
			}
			it2.advance();
		}
		score = std::max(score_floor, std::min(score_cap, score));
		if(passfail && score < 100)
			score = 0;
		if(!noscore)
		{
			meta += "Preliminary score: " + to_str(score) + "/100";
		}
		meta += "\n";
		cout << meta;
		cout.flush();

		// Save the meta data
		string s = sPath;
		s += "meta.txt";
		GFile::saveFile(meta.c_str(), meta.length(), s.c_str());

		// Output the meta data
		response << meta;
	}

	virtual void makePage(const char* szUrl, GDynamicPageSession* pSession, ostream& response)
	{
		int status;
		if(waitpid(m_pid, &status, WNOHANG) == m_pid)
		{
			int retval = 666;
			if(WIFEXITED(status))
				retval = WEXITSTATUS(status);
			string sStdOut = m_pipeOut.read(655360);
			string sStdErr = m_pipeErr.read(655360);

			// Display the output
			response << "<html><body>\n";
			response << "</pre>\n<h2>stdout (output)";
			if(sStdOut.size() >= 655360)
				response << " (truncated due to excessive length)";
			response << "</h2>\n<pre>";
			response << sStdOut;
			response << "</pre>\n<h2>stderr</h2>";
			if(sStdErr.size() >= 655360)
				response << " (truncated due to excessive length)";
			response << "\n<pre>";
			response << sStdErr;
			response << "</pre>\n<h2>return code</h2>\n<pre>";
			response << to_str(retval) << "\n";
			response << "</pre>\n<h2>Tentative evaluation</h2>\n<pre>";
			try
			{
				checkResults(m_projectNumber, m_meta, sStdOut, sStdErr, m_s, response);
			}
			catch(Ex& e)
			{
				response << "An error occurred while trying to check the results: " << e.what();
				response << "<br>\n<br>\nThis probably indicates a bug in the autograder script. You should probably e-mail your work to the instructor, and let him know that this thing isn't working.<br>\n";
				return;
			}

			response << "</pre>\n<br><br>\n";
			response << "</body></html>\n";

			// Send an email to notify the administrator
//			GSmtp::sendEmail("username@domain.com", "automated@nowhere.com", "The following file has been uploaded", meta.c_str(), "smtp.domain.com");
			m_pServer->nukeJob((ViewJob*)this);
		}
		else
		{
			// Wait a few seconds, then refresh
			response << "<html><head><meta http-equiv=\"refresh\" content=\"5;url=";
			response << m_jobname;
			response << "\"></head><body>\n";
			response << "Still working on it...<br><br>\n";
			response << to_str(m_counter++);
			response << "</body></html>\n";
		}
	}
};


// ------------------------------------------------------

// virtual
void Connection::handleRequest(GDynamicPageSession* pSession, ostream& response)
{
	if(strcmp(m_szUrl, "/favicon.ico") == 0)
		return;
	for(size_t i = 0; i < ((Server*)m_pServer)->m_jobs.size(); i++)
	{
		if(strcmp(m_szUrl, ((Server*)m_pServer)->m_jobs[i]->jobName().c_str()) == 0)
		{
			((Server*)m_pServer)->m_jobs[i]->makePage(m_szUrl, pSession, response);
			return;
		}
	}
	((Server*)m_pServer)->makePage(m_szUrl, pSession, response);
}

// ------------------------------------------------------

Server::Server(int port, GRand* pRand) : GDynamicPageServer(port, pRand)
{
	char buf[300];
	GTime::asciiTime(buf, 256, false);
	cout << "Server starting at: " << buf << "\n";
	GApp::appPath(buf, 256, true);
	strcat(buf, "web/");
	GFile::condensePath(buf);
	m_basePath = buf;
}

// virtual
Server::~Server()
{
}

void Server::makePage(const char* szUrl, GDynamicPageSession* pSession, ostream& response)
{
	string fn = "/home/sandbox/";
	fn += (szUrl + 1);
	fn += ".json";
	if(!GFile::doesFileExist(fn.c_str()))
	{
		response << "Sorry, no script for " << szUrl << " has been found. Please contact the instructor";
		return;
	}
	GDom* pDoc = new GDom();
	Holder<GDom> hDoc(pDoc);
	try
	{
		pDoc->loadJson(fn.c_str());
	}
	catch(Ex& e)
	{
		response << "Error while parsing the requirements for " << szUrl << ": " << e.what();
		return;
	}
	const GDomNode* pNode = pDoc->root();

	if(pSession->paramsLen() <= 0)
	{
		// Show the upload form
		response << "<html><body>\n";
		response << "<h2>Project Submisison Form</h2>\n";
		response << "<p>This is where you submit your projects. You may submit multiple times. If you cannot get it to work, don't panic, just e-mail your code to the instructor.</p>\n";
		response << "<form method='post' enctype='multipart/form-data' onsubmit=\"return validateForm()\"><table>\n";
		response << "	<tr><td align=right>What is your first name?</td><td><input type=text name=name required></td></tr>\n";
		response << "	<tr><td align=right>What is your last name?</td><td><input type=text name=surname required></td></tr>\n";
		response << "	<tr><td align=right>Which project would you like to submit?</td><td><select name=project>\n";

		GDomListIterator it(pNode);
		size_t index = 1;
		while(it.remaining() > 0)
		{
			GDomNode* pProj = it.current();
			response << "		<option value=\"" << to_str(index) << "\">";
			response << pProj->field("name")->asString();
			response << "</option>\n";
			index++;
			it.advance();
		}
		response << "	</select></td></tr>\n";
		response << "	<tr><td align=right>Zip or Tarball to upload:</td><td><input type=file name=upfile></td></tr>\n";
		response << "	<tr><td align=right>How many hours of your time did this project take? (optional):</td><td><input type=number name=hours_spent min='0' max='100'></td></tr>\n";
		response << "	<tr><td align=right><input type=submit value=Submit></td><td>(Please click only once. It takes a while to respond.)</td></tr>\n";
		response << "</table></form><br><br>\n";
		response << "Jobs currently running: " << to_str(jobCount()) << "\n";
		response << "<br><br><br><br><h2>How this thing works</h2>\n";
		response << "<ol><li>You submit a zip or tb2 file.</li>\n";
		response << "<li>It is unzipped on a virtual server.</li>\n";
		response << "<li>A time-out timer is started, and it switches to a user with limited permissions.</li>\n";
		response << "<li>It looks for a file named \"build.bash\" and executes it.</li>\n";
		response << "<li>Everything printed to stdout throughout the entire process is gathered and displayed for you.</li>\n";
		response << "<li>The auto-grader searches the output for lines of interest.</li>\n";
		response << "<li>Your code and output is archived for the instructor to examine.</li></ol>\n";
		response << "</body></html>\n";
	}
	else
	{
		// Find the student's name and surname
		string sName = "";
		string sSurname = "";
		{
			size_t nameStart, nameLen, valueStart, valueLen, filenameStart, filenameLen;
			GHttpMultipartParser parser(pSession->params(), pSession->paramsLen());
			while(parser.next(&nameStart, &nameLen, &valueStart, &valueLen, &filenameStart, &filenameLen))
			{
				if(nameStart >= 0 && strncmp(pSession->params() + nameStart, "name", nameLen) == 0)
					sName.assign(pSession->params() + valueStart, valueLen);
				if(nameStart >= 0 && strncmp(pSession->params() + nameStart, "surname", nameLen) == 0)
					sSurname.assign(pSession->params() + valueStart, valueLen);
			}
		}

		// Extract the meta string
		string timestamp;
		GTime::appendTimeStampValue(&timestamp, "-", "_", "-", false);
		timestamp += "_";
		timestamp += to_str(prng()->next(10000));
		string meta = timestamp;
		meta += ",";
		size_t nameStart, nameLen, valueStart, valueLen, filenameStart, filenameLen;
		GHttpMultipartParser parser(pSession->params(), pSession->paramsLen());
		size_t projectNumber = 0;
		while(parser.next(&nameStart, &nameLen, &valueStart, &valueLen, &filenameStart, &filenameLen))
		{
			if(filenameStart != (size_t)-1 && filenameLen > 0)
			{
				string fn;
				fn.assign(pSession->params() + filenameStart, filenameLen);
				fn = scrub_string(fn);
				meta += fn;
			}
			else
			{
				string sName;
				if(nameStart >= 0)
					sName.assign(pSession->params() + nameStart, nameLen);
				else
					sName = "?";
				meta += sName;
				meta += "=";
				string sValue;
				sValue.assign(pSession->params() + valueStart, valueLen);
				meta.append(sValue);
				if(strcmp(sName.c_str(), "project") == 0)
					projectNumber = atoi(sValue.c_str());
			}
			meta += ",";
		}

		// Make a folder for this upload
		string section = (szUrl + 1);
		string s = m_basePath;
		s += "uploads/";
		s += scrub_string(section); // a sub-folder with the class name
		s += "/a";
		s += to_str(projectNumber);
		s += "_";
		s += scrub_string(sSurname); // student's surname
		s += "_";
		s += scrub_string(sName); // student's first name
		s += "_";
		s += timestamp;
		s += "/";
		GFile::makeDir(s.c_str());

		// Extract and save the uploaded data
		GHttpMultipartParser parser2(pSession->params(), pSession->paramsLen());
		string sFilename;
		while(parser2.next(&nameStart, &nameLen, &valueStart, &valueLen, &filenameStart, &filenameLen))
		{
			if(filenameStart != (size_t)-1 && filenameLen > 0)
			{
				string fn;
				fn.assign(pSession->params() + filenameStart, filenameLen);
				fn = scrub_string(fn);
				sFilename = s;
				sFilename += fn;
				GFile::saveFile(pSession->params() + valueStart, valueLen, sFilename.c_str());
			}
		}

		string sBatch = "/bin/bash ";
		sBatch += m_basePath;
		sBatch += "check.bash ";
		sBatch += sFilename;

		string sJob = "/";
		sJob += to_str(prng()->next(100000000));
		addJob(new ViewJob(sJob, sBatch, projectNumber, meta, s, this, hDoc.release()));

		response << "<html><head><meta http-equiv=\"refresh\" content=\"5;url=";
		response << sJob;
		response << "\"></head><body>\n";
		response << "Submission received. Starting to check it...</body></html>\n";
	}
}


void getLocalStorageFolder(char* buf)
{
	if(!GFile::localStorageDirectory(buf))
		throw Ex("Failed to find local storage folder");
	strcat(buf, "/.autopassoff/");
	GFile::makeDir(buf);
	if(!GFile::doesDirExist(buf))
		throw Ex("Failed to create folder in storage area");
}

// virtual
void Server::onEverySixHours()
{
}

// virtual
void Server::onStateChange()
{
}

// virtual
void Server::onShutDown()
{
}

void Server::addJob(ViewJob* pJob)
{
	// Flush out old jobs
	time_t now;
	time(&now);
	for(size_t i = 0; i < m_jobs.size(); i++)
	{
		if(now - m_jobs[i]->timeStamp() > 600)
		{
			delete(m_jobs[i]);
			m_jobs.erase(m_jobs.begin() + i);
			i--;
		}
	}

	// Add this job
	m_jobs.push_back(pJob);
}

void Server::nukeJob(ViewJob* pJob)
{
	for(size_t i = 0; i < m_jobs.size(); i++)
	{
		if(m_jobs[i] == pJob)
		{
			m_jobs.erase(m_jobs.begin() + i);
			break;
		}
	}
	delete(pJob);
}





void OpenUrl(const char* szUrl)
{
#ifdef WINDOWS
	// Windows
	ShellExecute(NULL, NULL, szUrl, NULL, NULL, SW_SHOW);
#else
#ifdef DARWIN
	// Mac
	GTEMPBUF(char, pBuf, 32 + strlen(szUrl));
	strcpy(pBuf, "open ");
	strcat(pBuf, szUrl);
	strcat(pBuf, " &");
	system(pBuf);
#else // DARWIN
	GTEMPBUF(char, pBuf, 32 + strlen(szUrl));

	// Gnome
	strcpy(pBuf, "gnome-open ");
	strcat(pBuf, szUrl);
	if(system(pBuf) != 0)
	{
		// KDE
		//strcpy(pBuf, "kfmclient exec ");
		strcpy(pBuf, "konqueror ");
		strcat(pBuf, szUrl);
		strcat(pBuf, " &");
		if(system(pBuf) != 0)
			cout << "Failed to open " << szUrl << ". Please open it manually.\n";
	}
#endif // !DARWIN
#endif // !WINDOWS
}

void LaunchBrowser(const char* szAddress)
{
	int addrLen = strlen(szAddress);
	GTEMPBUF(char, szUrl, addrLen + 20);
	strcpy(szUrl, szAddress);
	strcpy(szUrl + addrLen, "/main.hbody");
	if(!GApp::openUrlInBrowser(szUrl))
	{
		cout << "Failed to open the URL: " << szUrl << "\nPlease open this URL manually.\n";
		cout.flush();
	}
}

void doit(void* pArg)
{
	int port = 8989;
	unsigned int seed = getpid() * (unsigned int)time(NULL);
	GRand prng(seed);
	Server server(port, &prng);
	LaunchBrowser(server.myAddress());

	// Pump incoming HTTP requests (this is the main loop)
	server.go();
	cout << "Goodbye.\n";
}

void doItAsDaemon()
{
	char path[300];
	getLocalStorageFolder(path);
	string s1 = path;
	s1 += "stdout.log";
	string s2 = path;
	s2 += "stderr.log";
	GApp::launchDaemon(doit, path, s1.c_str(), s2.c_str());
	cout << "Daemon running.\n	stdout >> " << s1.c_str() << "\n	stderr >> " << s2.c_str() << "\n";
}

int main(int nArgs, char* pArgs[])
{
	int nRet = 1;
	try
	{
#ifdef _DEBUG
		doit(NULL);
#else
		doItAsDaemon();
#endif
	}
	catch(std::exception& e)
	{
		cerr << e.what() << "\n";
	}
	return nRet;
}
