// -------------------------------------------------------------
// The contents of this file may be distributed under the CC0
// license (http://creativecommons.org/publicdomain/zero/1.0/).
// -------------------------------------------------------------

#include <exception>
#include <iostream>
#include <GClasses/GApp.h>
#include <GClasses/GError.h>
#include <string>
#include <fstream>

using namespace GClasses;
using std::cerr;
using std::cout;
using std::string;
using std::ofstream;

const char* g_months[] = {
	"January",
	"February",
	"March",
	"April",
	"May",
	"June",
	"July",
	"August",
	"September",
	"October",
	"November",
	"December"
};

//                   J   F   M   A   M   J   J   A   S   O   N   D
size_t g_days[] = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };

size_t daysInMonth(size_t month, size_t year)
{
	if(month == 1 && year % 4 == 0)
		return 29;
	else
		return g_days[month];
}

void doit()
{
	size_t year = 2012;
	size_t day = 0; // Sunday

	while(year < 2042)
	{
		string sFilename = to_str(year);
		sFilename += ".html";
		std::ofstream s;
		s.exceptions(std::ios::failbit|std::ios::badbit);
		s.open(sFilename.c_str(), std::ios::binary);

		s << "<html>\n";
		s << "<head>\n	<style>\n";
		s << "	body {\n";
		s << "		background-color: #c0c0b0;\n";
		s << "	}\n";
		s << "	.blank {\n";
		s << "		background-color: gray;\n";
		s << "	}\n";
		s << "	.active {\n";
		s << "		background-color: #e0e0c0;\n";
		s << "	}\n";
		s << "</style>\n<meta http-equiv=\"content-type\" content=\"text/html; charset=ISO-8859-1\">\n<title>Calendar</title>\n</head>\n";
		s << "<body>\n<table align=center width=1000px><tr><td>\n\n";

		for(size_t month = 0; month < 12; month++)
		{
			s << "<a id=\"" << g_months[month] << "\"><h2>" << g_months[month] << "</h2>\n";
			s << "<table width=\"100%\" border=1 class=\"active\">\n";
			s << "<tr><td width=\"10%\">Sunday</td><td width=\"16%\">Monday</td><td width=\"16%\">Tuesday</td><td width=\"16%\">Wednesday</td><td width=\"16%\">Thursday</td><td width=\"16%\">Friday</td><td width=\"10%\">Saturday</td></tr>\n";
			
			size_t date = 1;
			while(date <= daysInMonth(month, year))
			{
				s << "<tr valign=top>\n";

				size_t daysLeft = 7;
				if(day > 0)
				{
					s << "<td class=\"blank\" colspan=\"" << to_str(day) << "\"><br><br><br><br><br><br><br><br><br><br></td>\n";
					daysLeft -= day;
				}
				while(daysLeft > 0 && date <= daysInMonth(month, year))
				{
					s << "	<td>" << to_str(date) << "<br><br>";
					if(daysLeft == 7)
						s << "<br><br><br><br><br><br><br>";
					s << "</td>\n";
					daysLeft--;
					date++;
					if(++day >= 7)
						day = 0;
				}
				if(daysLeft > 0)
					s << "	<td class=\"blank\" colspan=\"" << to_str(daysLeft) << "\">&nbsp;</td>\n";
				s << "</tr>\n";
			}
			s << "</table>\n\n";
		}
		
		s << "</td></tr></table></body></html>\n";

		s.close();
		year++;
	}
}

int main(int argc, char *argv[])
{
	int nRet = 0;
	try
	{
		doit();
	}
	catch(const std::exception& e)
	{
		cerr << e.what() << "\n";
		nRet = 1;
	}

	return nRet;
}

