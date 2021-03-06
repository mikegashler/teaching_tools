// -------------------------------------------------------------
// The contents of this file may be distributed under the CC0
// license (http://creativecommons.org/publicdomain/zero/1.0/).
// -------------------------------------------------------------

#include <exception>
#include <iostream>
#include <string.h>
#include <memory>
#include <GClasses/GApp.h>
#include <GClasses/GError.h>
#include <GClasses/GTokenizer.h>
#include <GClasses/GFile.h>
#include <GClasses/GPriorityQueue.h>
#include <vector>
#include <set>
#include <cmath>
#include <sstream>
#include <string>
#include <map>

using namespace GClasses;
using std::cerr;
using std::cout;
using std::vector;
using std::set;
using std::string;
using std::stringstream;
using std::pair;
using std::map;
using std::unique_ptr;

class MyTokenizer : public GTokenizer
{
public:
	GCharSet m_symbol, m_whitespace, m_identifier, m_operator, m_signeddigits, m_digits, m_float;

	MyTokenizer(const char* szFilename) : GTokenizer(szFilename),
		m_symbol("\t\r a-zA-Z0-9_"),
		m_whitespace("\t\r\n "),
		m_identifier("a-zA-Z0-9_"),
		m_operator("<>=+*/&^|%!~"), // '-' is deliberately missing because it is special
		m_signeddigits("-0-9"),
		m_digits("0-9"),
		m_float(".0-9e") // '-' is deliberatly missing here
		{}

	virtual ~MyTokenizer() {}

	void skip_to_next_line()
	{
		while(true)
		{
			char c = peek();
			advance(1);
			if(c == '\n' || c == '\r' || c == '\0')
				break;
		}
	}

	void tokenize(vector<string>& tokens, vector<size_t>& lines)
	{
		while(true)
		{
			// Skip whitespace
			while(true)
			{
				if(!has_more())
					break;
				char c = peek();
				if(!m_whitespace.find(c))
					break;
				advance(1);
			}
			if(!has_more())
				break;

			char c = peek();
			if(c == '/' && peek(1) == '/') // line comment
			{
				advance(2);
				skip_to_next_line();
			}
			else if(c == '/' && peek(1) == '*') // block comment
			{
				advance(2);
				while(true)
				{
					c = peek();
					if(c == '\0')
						break;
					if(c == '*' && peek(1) == '/')
					{
						advance(2);
						break;
					}
					advance(1);
				}
			}
			else if(c == '-' && peek(1) == '>') // -> indirection
			{
				tokens.push_back("->");
				lines.push_back(line());
				advance(2);
			}
			else if(c == ':' && peek(1) == ':') // ::
			{
				tokens.push_back("::");
				lines.push_back(line());
				advance(2);
			}
			else if(c == '\\' && peek(1) != '\0') // escaped character
			{
				string s = "\\";
				advance(1);
				s += peek();
				advance(1);
				tokens.push_back(s);
				lines.push_back(line());
			}
			else if(c == '-' && m_operator.find(peek(1))) // -= and ->
			{
				string s = "-";
				advance(1);
				while(m_operator.find(peek()))
				{
					s += peek();
					advance(1);
				}
				tokens.push_back(s);
				lines.push_back(line());
			}
			else if(c == '-' && (m_signeddigits.find(peek(1)))) // negative constant values
			{
				string s = "-";
				advance(1);
				while(m_float.find(peek()))
				{
					s += peek();
					advance(1);
				}
				tokens.push_back(s);
				lines.push_back(line());
			}
			else if(c == '.' && m_digits.find(peek(1))) // floating point values beginning with '.'
			{
				string s = ".";
				advance(1);
				while(m_float.find(peek()))
				{
					s += peek();
					advance(1);
				}
				tokens.push_back(s);
				lines.push_back(line());
			}
			else if(m_operator.find(c))
			{
				tokens.push_back(nextWhile(m_operator));
				lines.push_back(line());
			}
			else if(m_identifier.find(c))
			{
				const char* szTok = nextWhile(m_identifier);
				if(strcmp(szTok, "import") == 0) // Treat "import" lines like comments
					skip_to_next_line();
				else
				{
					tokens.push_back(szTok);
					lines.push_back(line());
				}
			}
			else
			{
				string s = "";
				s += c;
				tokens.push_back(s);
				lines.push_back(line());
				advance(1);
			}
		}
	}
};

set<string>* g_keywords = nullptr;


bool isAlpha(char c)
{
	if(c >= 'a' && c <= 'z') return true;
	if(c >= 'A' && c <= 'Z') return true;
	if(c == '_') return true;
	return false;
}

bool isNumber(string& s)
{
	size_t i = 0;
	while(i < s.length() && (s[i] == '-' || s[i] == '.'))
		i++;
	if(i >= s.length())
		return false;
	if(s[i] >= '0' && s[i] <= '9')
		return true;
	return false;
}



class CodeNode
{
public:
	string m_token;
	size_t m_line;
	size_t m_size;
	CodeNode* m_firstChild;
	CodeNode* m_lastChild;
	CodeNode* m_nextSibling;
	CodeNode* m_prevSibling;

	CodeNode(string tok, size_t line)
	: m_token(tok),
	m_line(line),
	m_size((size_t)-1),
	m_firstChild(nullptr),
	m_lastChild(nullptr),
	m_nextSibling(nullptr),
	m_prevSibling(nullptr)
	{
	}

	void addChild(CodeNode* pChild)
	{
		m_size = (size_t)-1;
		if(m_lastChild)
			m_lastChild->m_nextSibling = pChild;
		pChild->m_prevSibling = m_lastChild;
		m_lastChild = pChild;
		if(!m_firstChild)
			m_firstChild = pChild;
	}

	CodeNode* dropFirstChild()
	{
		m_size = (size_t)-1;
		if(!m_firstChild)
			return nullptr;
		CodeNode* pOrphan = m_firstChild;
		if(pOrphan->m_nextSibling)
		{
			m_firstChild = pOrphan->m_nextSibling;
			pOrphan->m_nextSibling->m_prevSibling = nullptr;
			pOrphan->m_nextSibling = nullptr;
		}
		else
		{
			m_firstChild = nullptr;
			m_lastChild = nullptr;
		}
		return pOrphan;
	}

	void takeChildren(CodeNode* pPeer)
	{
		while(pPeer->m_firstChild)
			addChild(pPeer->dropFirstChild());
	}

	size_t size()
	{
		if(m_size == (size_t)-1)
		{
			m_size = 1;
			for(CodeNode* pChild = m_firstChild; pChild != nullptr; pChild = pChild->m_nextSibling)
				m_size += pChild->size();
		}
		return m_size;
	}

	// If normalize is true, this will replace all numbers with "number" and all identifiers with "identifier"
	void print(size_t depth, bool normalize)
	{
		for(size_t i = 0; i < depth; i++)
			cout << "  ";
		if(normalize)
		{
			if(isNumber(m_token))
				cout << "number";
			else if(isAlpha(m_token[0]))
			{
				if(isKeyWord(m_token))
					cout << m_token;
				else
					cout << "identifier";
			}
			else
				cout << m_token;
		}
		else
			cout << m_token;
		cout << "\n";
		for(CodeNode* pChild = m_firstChild; pChild != nullptr; pChild = pChild->m_nextSibling)
			pChild->print(depth + 1, normalize);
	}

	void stringify(std::stringstream& ss)
	{
		if(isNumber(m_token))
			ss << "#";
		else if(isAlpha(m_token[0]))
		{
			if(isKeyWord(m_token))
				ss << m_token;
			else
				ss << "id";
		}
		else
			ss << m_token;
		if(m_firstChild)
		{
			ss << "`";
			for(CodeNode* pChild = m_firstChild; pChild != nullptr; pChild = pChild->m_nextSibling)
			{
				pChild->stringify(ss);
				ss << ";";
			}
		}
	}

	static bool isKeyWord(string& s)
	{
		if(!g_keywords)
		{
			g_keywords = new set<string>();
			g_keywords->insert("ArrayList");
			g_keywords->insert("boolean");
			g_keywords->insert("break");
			g_keywords->insert("case");
			g_keywords->insert("catch");
			g_keywords->insert("class");
			g_keywords->insert("double");
			g_keywords->insert("else");
			g_keywords->insert("extends");
			g_keywords->insert("File");
			g_keywords->insert("finally");
			g_keywords->insert("for");
			g_keywords->insert("Graphics");
			g_keywords->insert("if");
			g_keywords->insert("Image");
			g_keywords->insert("implements");
			g_keywords->insert("int");
			g_keywords->insert("LinkedList");
			g_keywords->insert("MouseEvent");
			g_keywords->insert("new");
			g_keywords->insert("NULL");
			g_keywords->insert("null");
			g_keywords->insert("nullptr");
			g_keywords->insert("private");
			g_keywords->insert("protected");
			g_keywords->insert("public");
			g_keywords->insert("return");
			g_keywords->insert("static");
			g_keywords->insert("super");
			g_keywords->insert("System");
			g_keywords->insert("throws");
			g_keywords->insert("try");
			g_keywords->insert("void");
			g_keywords->insert("while");
		}
		if(g_keywords->find(s) == g_keywords->end())
			return false;
		else
			return true;
	}

	static CodeNode* parseImport(vector<string>& toks, vector<size_t>& lines, size_t& pos)
	{
		CodeNode* pNode = new CodeNode(toks[pos], lines[pos]); // "import"
		pos++;
		while(true)
		{
			if(pos >= toks.size())
				break;
			if(toks[pos].compare(";") == 0)
			{
				pos++;
				break;
			}
			pNode->addChild(new CodeNode(toks[pos], lines[pos]));
			pos++;
		}
		return pNode;
	}

	static CodeNode* parseParens(vector<string>& toks, vector<size_t>& lines, size_t& pos)
	{
		CodeNode* pNode = new CodeNode(toks[pos], lines[pos]); // "("
		pos++;
		while(true)
		{
			if(pos >= toks.size())
				break;
			if(toks[pos].compare(")") == 0)
				break;
			pNode->addChild(parseExpression(toks, lines, pos));
		}
		return pNode;
	}

	static CodeNode* parseBrackets(vector<string>& toks, vector<size_t>& lines, size_t& pos)
	{
		CodeNode* pNode = new CodeNode(toks[pos], lines[pos]); // "["
		pos++;
		while(true)
		{
			if(pos >= toks.size())
				break;
			if(toks[pos].compare("]") == 0)
				break;
			pNode->addChild(parseExpression(toks, lines, pos));
		}
		return pNode;
	}

	static CodeNode* parseString(vector<string>& toks, vector<size_t>& lines, size_t& pos)
	{
		pos++;
		while(pos < toks.size() && !toks[pos].compare("\"") == 0)
			pos++;
		return new CodeNode("s", lines[pos]);
	}

	static CodeNode* parseBoundedExpr(vector<string>& toks, vector<size_t>& lines, size_t pos, size_t end)
	{
		// Find the operator with lowest precedence
		size_t op = findLowestPrecedenceOperation(toks, lines, pos, end);
		if(op < end)
		{
			CodeNode* pNode = parseOperation(toks, lines, pos, op, end);
			GAssert(pos == end);
			return pNode;
		}

		// Check for a reserved word
		op = findTypeDef(toks, lines, pos, end);
		if(op < end)
		{
			CodeNode* pNode = parseTypeDef(toks, lines, pos, op, end);
			GAssert(pos == end);
			return pNode;
		}

		// Check for a declaration
		size_t nonDecl = countNonDeclarationTokens(toks, lines, pos, end);
		if(end > pos && end - pos > 1 && nonDecl == 0)
		{
			CodeNode* pNode = parseDeclaration(toks, lines, pos, end);
			GAssert(pos == end);
			return pNode;
		}

		// Make the CodeNode for the variable or constant expression
		CodeNode* pNode = new CodeNode(toks[end - 1], lines[end - 1]);
		if(pos + 1 < end)
		{
			CodeNode* pQualifiers = new CodeNode(":", lines[pos]);
			pNode->addChild(pQualifiers);
			for(size_t i = pos; i + 2 < end; i++)
				pQualifiers->addChild(new CodeNode(toks[i], lines[i]));
		}
		return pNode;
	}

	static size_t findMatchingParen(vector<string>& toks, vector<size_t>& lines, size_t pos, size_t end)
	{
		size_t paren_nests = 0;
		for(size_t i = pos; i < end; i++)
		{
			if(toks[i].compare("(") == 0)
				paren_nests++;
			else if(toks[i].compare(")") == 0)
			{
				if(paren_nests == 0)
					return i;
				paren_nests--;
			}
		}
		return end;
	}

	static size_t findNextArgSeparator(vector<string>& toks, vector<size_t>& lines, size_t pos, size_t end)
	{
		size_t paren_nests = 0;
		for(size_t i = pos; i < end; i++)
		{
			if(toks[i].compare("(") == 0)
				paren_nests++;
			else if(toks[i].compare(")") == 0)
			{
				if(paren_nests == 0)
					return i;
				paren_nests--;
			}
			else if(paren_nests == 0)
			{
				if(toks[i].compare(",") == 0)
					return i;
				else if(toks[i].compare(";") == 0)
					return i;
			}
		}
		return end;
	}

	static size_t findExpressionEnd(vector<string>& toks, vector<size_t>& lines, size_t pos)
	{
		size_t paren_nests = 0;
		for(size_t i = pos; i < toks.size(); i++)
		{
			if(i >= toks.size())
				return i;
			else if(toks[i].compare("(") == 0)
				paren_nests++;
			else if(toks[i].compare(")") == 0)
			{
				if(paren_nests == 0)
					return i;
				paren_nests--;
				if(paren_nests == 0)
					return i + 1;
			}
			else if(paren_nests == 0 && toks[i].compare(";") == 0)
				return i;
			else if(toks[i].compare("{") == 0)
				return i;
			else if(toks[i].compare("}") == 0)
				return i;
		}
		return toks.size();
	}

	static size_t findLowestPrecedenceOperation(vector<string>& toks, vector<size_t>& lines, size_t pos, size_t end)
	{
		size_t pri = 100;
		size_t paren_nests = 0;
		size_t brace_nests = 0;
		size_t ret = end;
		for(size_t i = pos; i < end; i++)
		{
			if(toks[i].compare("(") == 0)
				paren_nests++;
			else if(toks[i].compare(")") == 0)
				paren_nests--;
			else if(toks[i].compare("{") == 0)
				brace_nests++;
			else if(toks[i].compare("}") == 0)
				brace_nests--;
			else if(paren_nests == 0 && brace_nests == 0)
			{
				if(toks[i].compare("||") == 0 && pri > 0)
				{
					pri = 0;
					ret = i;
				}
				else if(toks[i].compare("&&") == 0 && pri > 1)
				{
					pri = 1;
					ret = i;
				}
				else if(toks[i].find("=") != string::npos && pri > 4)
				{
					pri = 4;
					ret = i;
				}
				else if(toks[i].compare("+") == 0 && pri > 8)
				{
					pri = 8;
					ret = i;
				}
				else if(toks[i].compare("%") == 0 && pri > 10)
				{
					pri = 10;
					ret = i;
				}
				else if(toks[i].compare("++") == 0 && pri > 12)
				{
					pri = 12;
					ret = i;
				}
				else if(toks[i].compare("--") == 0 && pri > 12)
				{
					pri = 12;
					ret = i;
				}
				else if(i + 1 < toks.size() && toks[i + 1].compare("(") == 0 && (isAlpha(toks[i][0]) || toks[i].compare(">") == 0) && pri > 20) // call
				{
					pri = 20;
					ret = i;
				}
			}
		}
		return ret;
	}

	static size_t findTypeDef(vector<string>& toks, vector<size_t>& lines, size_t pos, size_t end)
	{
		for(size_t i = pos; i < end; i++)
		{
			if(toks[i].compare("class") == 0)
				return i;
			else if(toks[i].compare("enum") == 0)
				return i;
			else if(toks[i].compare("struct") == 0)
				return i;
		}
		return end;
	}

	static CodeNode* parseCall(vector<string>& toks, vector<size_t>& lines, size_t& pos, size_t op, size_t end)
	{
		CodeNode* pNode = new CodeNode(toks[op], lines[op]);

		// Add qualifiers that precede the call
		if(op > pos)
		{
			CodeNode* pQualifiers = new CodeNode(":", lines[op]);
			pNode->addChild(pQualifiers);
			for(size_t i = pos; i < op; i++)
				pQualifiers->addChild(new CodeNode(toks[i], lines[i]));
		}
		pos = op + 1;
		if(pos < end && toks[pos].compare("(") == 0)
			pNode->addChild(parseArgs(toks, lines, pos, end));
		while(pos < end)
		{
			pNode->addChild(new CodeNode(toks[pos], lines[pos]));
			pos++;
		}
		return pNode;
	}

	static size_t countNonDeclarationTokens(vector<string>& toks, vector<size_t>& lines, size_t pos, size_t end)
	{
		size_t count = 0;
		size_t angle_nests = 0;
		for(size_t i = pos; i < end; i++)
		{
			if(toks[i].compare("<") == 0)
				angle_nests++;
			else if(toks[i].compare(">") == 0)
				angle_nests--;
			else if(angle_nests > 0 && toks[i].compare(",") == 0)
			{
			}
			else if(!isAlpha(toks[i][0]))
				count++;
		}
		return count;
	}

	static CodeNode* parseDeclaration(vector<string>& toks, vector<size_t>& lines, size_t& pos, size_t end)
	{
		CodeNode* pNode = new CodeNode(toks[end - 1], lines[end - 1]);
		for(size_t i = pos; i + 1 < end; i++)
			pNode->addChild(new CodeNode(toks[i], lines[end - 1]));
		GAssert(pos <= end);
		pos = end;
		return pNode;
	}

	static CodeNode* parseOperation(vector<string>& toks, vector<size_t>& lines, size_t& pos, size_t op, size_t end)
	{
		if(isAlpha(toks[op][0]))
			return parseCall(toks, lines, pos, op, end);

		CodeNode* pOp = new CodeNode(toks[op], lines[op]);
		if(op > pos)
			pOp->addChild(parseBoundedExpr(toks, lines, pos, op));
		if(op + 1 < end)
			pOp->addChild(parseBoundedExpr(toks, lines, op + 1, end));
		GAssert(pos <= end);
		pos = end;
		return pOp;
	}

	static CodeNode* parseTypeDef(vector<string>& toks, vector<size_t>& lines, size_t& pos, size_t op, size_t end)
	{
		CodeNode* pNode = new CodeNode(toks[op], lines[op]); // "class", "enum", "struct"
		if(pos < op)
		{
			CodeNode* pPre = new CodeNode("pre", lines[pos]);
			pNode->addChild(pPre);
			for(size_t i = pos; i < op; i++)
				pPre->addChild(new CodeNode(toks[i], lines[i]));
		}
		if(op + 1 < end)
		{
			CodeNode* pPost = new CodeNode("post", lines[op + 1]);
			pNode->addChild(pPost);
			for(size_t i = op + 1; i < end; i++)
				pPost->addChild(new CodeNode(toks[i], lines[i]));
		}
		pos = end;
		return pNode;
	}

	static CodeNode* parseExpression(vector<string>& toks, vector<size_t>& lines, size_t& pos)
	{
		// Check for keywords
		if(toks[pos].compare("if") == 0)
			return parseLoop(toks, lines, pos);
		if(toks[pos].compare("else") == 0)
			return parseLoop(toks, lines, pos);
		if(toks[pos].compare("for") == 0)
			return parseLoop(toks, lines, pos);
		if(toks[pos].compare("while") == 0)
			return parseLoop(toks, lines, pos);
		if(toks[pos].compare("switch") == 0)
			return parseLoop(toks, lines, pos);
		if(toks[pos].compare("do") == 0)
			return parseLoop(toks, lines, pos);
		if(toks[pos].compare("try") == 0)
			return parseLoop(toks, lines, pos);
		if(toks[pos].compare("catch") == 0)
			return parseLoop(toks, lines, pos);
		if(toks[pos].compare("finally") == 0)
			return parseLoop(toks, lines, pos);
		if(toks[pos].compare("import") == 0)
			return parseImport(toks, lines, pos);
		if(toks[pos].compare("{") == 0)
			return parseBlock(toks, lines, pos);
		if(toks[pos].compare("(") == 0)
			return parseParens(toks, lines, pos);
		if(toks[pos].compare("[") == 0)
			return parseBrackets(toks, lines, pos);
		if(toks[pos].compare("\"") == 0)
			return parseString(toks, lines, pos);

		// Find the end of the expression
		size_t end = std::max(pos + 1, findExpressionEnd(toks, lines, pos));
		CodeNode* pNode = parseBoundedExpr(toks, lines, pos, end);
		GAssert(pos <= end);
		pos = end;
		if(pos < toks.size() && toks[pos].compare("{") == 0)
			pNode->addChild(parseBlock(toks, lines, pos));
		return pNode;
	}

	static CodeNode* parseArgs(vector<string>& toks, vector<size_t>& lines, size_t& pos, size_t end)
	{
		size_t endParen = findMatchingParen(toks, lines, pos + 1, end);
		CodeNode* pNode = new CodeNode(toks[pos], lines[pos]); // "("
		pos++;
		while(pos < endParen)
		{
			size_t argEnd = findNextArgSeparator(toks, lines, pos, endParen);
			pNode->addChild(parseBoundedExpr(toks, lines, pos, argEnd));
			pos = std::min(endParen + 1, endParen);
		}
		if(toks[pos].compare(")") == 0)
			pos++;
		return pNode;
	}

	static CodeNode* parseLoop(vector<string>& toks, vector<size_t>& lines, size_t& pos)
	{
		CodeNode* pNode = new CodeNode(toks[pos], lines[pos]); // "if", "for", "while", "do"
		pos++;
		if(pos < toks.size() && toks[pos].compare("(") == 0)
		{
			size_t matchingParen = findMatchingParen(toks, lines, pos + 1, toks.size());
			pNode->addChild(parseArgs(toks, lines, pos, matchingParen + 1));
		}
		if(pos < toks.size())
			pNode->addChild(parseCommandBlock(toks, lines, pos));
		return pNode;
	}

	static CodeNode* parseBlock(vector<string>& toks, vector<size_t>& lines, size_t& pos)
	{
		CodeNode* pNode = new CodeNode(toks[pos], lines[pos]); // "{"
		pos++;
		while(true)
		{
			if(pos >= toks.size())
				break;
			if(toks[pos].compare("}") == 0)
			{
				pos++;
				break;
			}
			else if(toks[pos].compare(";") == 0)
				pos++;
			else
				pNode->addChild(parseExpression(toks, lines, pos));
		}
		return pNode;
	}

	static CodeNode* parseCommandBlock(vector<string>& toks, vector<size_t>& lines, size_t& pos)
	{
		if(toks[pos].compare("{") == 0)
			return parseBlock(toks, lines, pos);
		CodeNode* pNode = new CodeNode("{", lines[pos]);
		pNode->addChild(parseExpression(toks, lines, pos));
		return pNode;
	}

	static CodeNode* parseFile(vector<string>& toks, vector<size_t>& lines, size_t pos)
	{
		CodeNode* pNode = new CodeNode("file", toks.size() > 0 ? lines[pos] : 0);
		while(pos < toks.size())
		{
			if(toks[pos].compare(";") == 0)
				pos++;
			else
				pNode->addChild(parseExpression(toks, lines, pos));
		}
		return pNode;
	}

	static CodeNode* parse(const char* szFilename)
	{
		// Extract all the tokens from the file
		MyTokenizer tok(szFilename);
		vector<string> toks;
		vector<size_t> lines;
		tok.tokenize(toks, lines);

		// Parse the tokens
		return CodeNode::parseFile(toks, lines, 0);
	}

	static bool do_tokens_match(string& a, string& b)
	{
		if(a.compare(b) == 0)
			return true;
		if(isNumber(a) && isNumber(b))
			return true;
		if(isAlpha(a[0]) && isAlpha(b[0]))
		{
			if(isKeyWord(a) || isKeyWord(b))
				return false;
			return true;
		}
		return false;
	}

	void chunkify(map<string, CodeNode*>& chunks, size_t thresh)
	{
		if(size() < thresh)
		{
			std::stringstream ss;
			stringify(ss);
			string s = ss.str();
			chunks.insert(std::pair<string, CodeNode*>(s, this));
//cout << s << "\n";
		}
		else
		{
			for(CodeNode* pChild = m_firstChild; pChild; pChild = pChild->m_nextSibling)
				pChild->chunkify(chunks, thresh);
		}
	}

	size_t align_cost(CodeNode* pSrc, size_t max_cost, size_t depth)
	{
		// Don't waste time comparing nodes of totally different size
		if(size() + max_cost < pSrc->size() || pSrc->size() + max_cost < size())
			return max_cost;
		
		size_t cost = 0;
		if(!do_tokens_match(pSrc->m_token, m_token))
			cost++;

		// Make temporary vectors of all child nodes
		vector<CodeNode*> pool;
		for(CodeNode* pChild = m_firstChild; pChild != nullptr; pChild = pChild->m_nextSibling)
			pool.push_back(pChild);
		vector<CodeNode*> needles;
		for(CodeNode* pChild = pSrc->m_firstChild; pChild != nullptr; pChild = pChild->m_nextSibling)
			needles.push_back(pChild);

		// Seize the lowest-cost matches for each child of pSrc
		size_t maxMatchThresh = 0;
		while(needles.size() > 0)
		{
			size_t minSkippedCost = 10000000;
			for(size_t i = 0; i < needles.size(); i++)
			{
				size_t lowest_index = (size_t)-1;
				size_t lowest_cost = 10000000;
				for(size_t j = 0; j < pool.size(); j++)
				{
					size_t c = pool[j]->align_cost(needles[i], lowest_cost, depth + 1);
					if(c < lowest_cost)
					{
						lowest_cost = c;
						lowest_index = j;
						if(lowest_cost <= maxMatchThresh)
							break;
					}
				}
				if(lowest_index == (size_t)-1) // If there was nothing left in the pool to match with
				{
					cost += needles[i]->size(); // The cost is to absorb all tokens in needles[i]
					needles.erase(needles.begin() + i);
					i--;
				}
				else if(lowest_cost <= maxMatchThresh) // If this match is good enough
				{
					pool.erase(pool.begin() + lowest_index);
					needles.erase(needles.begin() + i);
					i--;
					cost += lowest_cost;
					if(cost >= minSkippedCost)
						needles.clear();
				}
				else
				{
					minSkippedCost = std::min(minSkippedCost, lowest_cost); // skip this one
				}
			}
			maxMatchThresh = minSkippedCost; // Raise the bar so we will get at least one match in the next pass
			if(needles.size() > 20) // If we have a lot of work to do
				maxMatchThresh *= 2; // hurry up by getting sloppy
		}

		// Add whatever is left in the pool to the cost
		for(size_t i = 0; i < pool.size(); i++)
			cost += pool[i]->size();

		return cost;
	}
};




class Submission
{
public:
	string name;
	string alphaname;
	CodeNode* pCodeNode;
	map<string, CodeNode*> chunks;

	Submission(string n)
	{
		pCodeNode = nullptr;
		name = n;
		for(size_t i = 0; i < n.length(); i++)
		{
			if((n[i] >= 'a' && n[i] <= 'z') || (n[i] >= 'A' && n[i] <= 'Z'))
				alphaname += n[i];
		}

		pCodeNode = processFolderRecursively(n.c_str());
		if(pCodeNode)
		{
			size_t thresh = 40;
			pCodeNode->chunkify(chunks, thresh);
		}
	}

	~Submission()
	{
		delete(pCodeNode);
	}

	static CodeNode* processFolderRecursively(const char* szFoldername)
	{
		CodeNode* pNode = nullptr;
		vector<string> files;
		GFile::fileListRecursive(files, szFoldername);
		for(size_t i = 0; i < files.size(); i++)
		{
			PathData pd;
			GFile::parsePath(files[i].c_str(), &pd);
			const char* ext = files[i].c_str() + pd.extStart;
			if(_stricmp(ext, ".cpp") == 0 ||
				_stricmp(ext, ".java") == 0 ||
				_stricmp(ext, ".h") == 0 ||
				_stricmp(ext, ".hpp") == 0 ||
				_stricmp(ext, ".php") == 0 ||
				_stricmp(ext, ".c") == 0 ||
				_stricmp(ext, ".py") == 0 ||
				_stricmp(ext, ".rb") == 0)
			{
				CodeNode* pTmp = CodeNode::parse(files[i].c_str());
				if(pNode)
				{
					pNode->takeChildren(pTmp);
					delete(pTmp);
				}
				else
					pNode = pTmp;
			}
		}
		return pNode;
	}

	double compare(Submission& that)
	{
		size_t matches = 0;
		for(map<string, CodeNode*>::iterator it = chunks.begin(); it != chunks.end(); it++)
		{
			map<string, CodeNode*>::iterator it2 = that.chunks.find(it->first);
			if(it2 != that.chunks.end())
				matches++;
		}
		return((double)matches / (chunks.size() + 1));
	}
};





class CheatFinder
{
protected:
	vector<Submission*> m_submissions;

public:
	CheatFinder()
	{
	}

	~CheatFinder()
	{
		for(size_t i = 0; i < m_submissions.size(); i++)
			delete(m_submissions[i]);
	}

	void parse(GArgReader& args)
	{
		CodeNode* a = Submission::processFolderRecursively(args.pop_string());
		a->print(0, false);
	}

	void normalize(GArgReader& args)
	{
		CodeNode* a = Submission::processFolderRecursively(args.pop_string());
		a->print(0, true);
	}

	void compare(GArgReader& args)
	{
		string folderA = args.pop_string();
		string folderB = args.pop_string();
		Submission a(folderA);
		Submission b(folderB);
		double d = a.compare(b);
		cout << to_str(d * 100.0) << "% within\n";
	}

	void parse_all_submissions(vector<string>& folders)
	{
		map<string,size_t> dupes;
		for(size_t i = 0; i < folders.size(); i++)
		{
			Submission* pS = new Submission(folders[i]);
			if(pS->pCodeNode)
			{
				//cout << "	" << folders[i] << "\n";
				map<string,size_t>::iterator it = dupes.find(pS->alphaname);
				if(it == dupes.end())
				{
					dupes[pS->alphaname] = m_submissions.size();
					m_submissions.push_back(pS);
				}
				else
				{
					size_t index = it->second;
					delete(m_submissions[index]);
					m_submissions[index] = pS;
				}
			}
			else
			{
				cout << "	(No code in " << folders[i] << ")\n";
				delete(pS);
			}
		}
	}

	void drop_common_chunks()
	{
		// Count all the chunks
		map<string,size_t> chunk_counts;
		for(size_t i = 0; i < m_submissions.size(); i++)
		{
			Submission* pSub = m_submissions[i];
			for(auto it = pSub->chunks.begin(); it != pSub->chunks.end(); it++)
			{
				auto it2 = chunk_counts.find(it->first);
				if(it2 == chunk_counts.end())
					chunk_counts.insert(std::pair<string,size_t>(it->first,1));
				else
					it2->second++;
			}
		}

		// Drop the infrequent chunks from chunk_counts
		size_t thresh = std::max(6ul, m_submissions.size() / 4);
		auto it = chunk_counts.begin();
		while(it != chunk_counts.end())
		{
			if(it->second < thresh)
			{
				auto condemned = it;
				it++;
				chunk_counts.erase(condemned);
			}
			else
				it++;
		}

		// Drop the frequent chunks from all of the submissions
		for(size_t i = 0; i < m_submissions.size(); i++)
		{
			Submission* pSub = m_submissions[i];
			auto it1 = pSub->chunks.begin();
			while(it1 != pSub->chunks.end())
			{
				const string& s = it1->first;
				auto it2 = chunk_counts.find(s);
				if(it2 == chunk_counts.end())
					it1++;
				else
				{
					auto condemned = it1;
					it1++;
					pSub->chunks.erase(condemned);
				}
			}
		}
	}

	void find_worst_offenders(GArgReader& args)
	{
		// Check parameters
		if(chdir(args.pop_string()) != 0)
			throw Ex("Failed to chdir");
		string subst1 = "";
		string subst2 = "";
		if(args.size() > 0)
		{
			subst1 = args.pop_string();
			if(args.size() > 0)
			{
				subst2 = args.pop_string();
				cout << "Comparing all pairs where the first folder contains the string \"" << subst1 << "\" and the second folder contains the string \"" << subst2 << "\"\n";
			}
			else
				cout << "Comparing all pairs where the first folder contains the string \"" << subst1 << "\"\n";
		}
		else
			cout << "Comparing all folder pairs\n";
		
		vector<string> folders;
		GFile::folderList(folders, ".");
		if(folders.size() < 2)
		{
			cout << "Expected two or more folders in the current directory.\n";
			return;
		}

		// Parse all the code
		cout << "Parsing...\n";
		parse_all_submissions(folders);
		drop_common_chunks();

		// Compare the data
		cout << "Comparing...\n";
		GSimplePriorityQueue< pair<size_t, size_t> > pq;
		for(size_t i = 0; i < m_submissions.size(); i++)
		{
			if(subst1.length() > 0 && m_submissions[i]->name.find(subst1) == string::npos)
				continue;
			for(size_t j = 0; j < m_submissions.size(); j++)
			{
				if(j == i)
					continue;
				if(subst2.length() > 0 && m_submissions[j]->name.find(subst2) == string::npos)
					continue;
				double overlap = m_submissions[i]->compare(*m_submissions[j]);
				//cout << to_str(overlap * 100.0) << "% of " << m_submissions[i]->name << " is in " << m_submissions[j]->name << "\n";
				pq.insert( pair<size_t, size_t>(i, j), -overlap);
			}
		}

		// Print the worst offenders
		cout << "Reporting...\n";
		for(size_t i = 0; i < 30; i++)
		{
			if(pq.size() == 0)
				break;
			double overlap = -pq.peekValue();
			const pair<size_t, size_t>& obj = pq.peekObject();
			cout << "	" << to_str(std::floor(overlap * 1000.0) * 0.1) << "% of " << m_submissions[obj.first]->name << " is in " << m_submissions[obj.second]->name << "\n";
			pq.pop();
		}
	}
};

void doit(GArgReader& args)
{
	args.pop_string();
	CheatFinder cf;
	if(args.if_pop("find"))
		cf.find_worst_offenders(args);
	else if(args.if_pop("compare"))
		cf.compare(args);
	else if(args.if_pop("parse"))
		cf.parse(args);
	else if(args.if_pop("normalize"))
		cf.normalize(args);
	else
	{
		cout << "\n";
		cout << "Usage:\n";
		cout << "  cheater [action]\n";
		cout << "    where [action] is any of:\n";
		cout << "\n";
		cout << "      find [folder] <sub1> <sub2>\n";
		cout << "        Compare the contents of each sub-folder in [folder]\n";
		cout << "        and report those that are most similar.\n";
		cout << "        The optional parameter <sub1> specifies a substring\n";
		cout << "        that must be found in the first folder name.\n";
		cout << "        The optional parameter <sub2> specifies a substring\n";
		cout << "        that must be found in the second folder name.\n";
		cout << "\n";
		cout << "      compare [folder1] [folder2]\n";
		cout << "        Compute the portion of [folder1] contained in [folder2].\n";
		cout << "        (Renamed tokens and whitespace adjustments\n";
		cout << "        are ignored.)\n";
		cout << "\n";
		cout << "      parse [folder]\n";
		cout << "        Print a parse tree representing all the code in\n";
		cout << "        [folder]\n";
		cout << "\n";
		cout << "      normalize [folder]\n";
		cout << "        Just like parse, except it normalizes numbers and\n";
		cout << "        identifiers\n";
		cout << "\n";
	}
}

int main(int argc, char *argv[])
{
#ifdef _DEBUG
	GApp::enableFloatingPointExceptions();
#endif
	int nRet = 0;
	try
	{
		GArgReader args(argc, argv);
		doit(args);
	}
	catch(const std::exception& e)
	{
		cerr << e.what() << "\n";
		nRet = 1;
	}

	return nRet;
}

