<?php session_start();
	$password = "change_me";
	$header = "<?php include 'header.php'; ?>";
	$footer = "<?php include 'footer.php'; ?>";
	if(isset($_GET['edit']))
	{
		print("<!doctype html><html><body>\n");
?>
<script>
// The following Javascript function was taken from http://pallieter.org/Projects/insertTab/ under the CC-BY license.
function insertTab(o, e)
{
	var kC = e.keyCode ? e.keyCode : e.charCode ? e.charCode : e.which;
	if (kC == 9 && !e.shiftKey && !e.ctrlKey && !e.altKey)
	{
		var oS = o.scrollTop;
		if (o.setSelectionRange)
		{
			var sS = o.selectionStart;
			var sE = o.selectionEnd;
			o.value = o.value.substring(0, sS) + "\t" + o.value.substr(sE);
			o.setSelectionRange(sS + 1, sS + 1);
			o.focus();
		}
		else if (o.createTextRange)
		{
			document.selection.createRange().text = "\t";
			e.returnValue = false;
		}
		o.scrollTop = oS;
		if (e.preventDefault)
		{
			e.preventDefault();
		}
		return false;
	}
	return true;
}

// This function checks whether a file with this name already exists.
<?php
$files = scandir(".");
print("var pages = [");
for($i = 0; $i < count($files); $i++)
{
	if($i > 0)
		print(",");
	
	print("\"" . $files[$i] . "\"");
}
print("];\n");
?>
function checkFilename(field)
{
	var found = false;
	for(var i = 0; i < pages.length; i++)
	{
		if(field.value == pages[i])
			found = true;
	}
	var el = document.getElementById("exists");
	if(found)
		el.style.display = 'block';
	else
		el.style.display = 'none';
	return false;
}
</script>
<?php		$pagename = htmlentities($_GET['edit']);
		$lastslash = strrpos($pagename, '/');
		if($lastslash !== FALSE)
			die("bogus pagename: " . $pagename);
		if($pagename == "edit.php")
			die("security violation");
		$contents = file_get_contents($pagename);
		$headerpos = strpos($contents, $header);
		$footerpos = strpos($contents, $footer);
		if($headerpos === FALSE || $footerpos === FALSE)
			die("could not find the expected header and footer");
		$headerpos += strlen($header);
		$contents = substr($contents, $headerpos, $footerpos - $headerpos);
		if($contents === FALSE)
			die("failed to load the file: " . $pagename);
		print("<form action=\"edit.php\" method=\"post\" id=\"editform\">\n");
		print("Filename:<br>\n");
		print("	<input type=\"text\" name=\"page\" value=\"" . $pagename . "\" onKeyUp=\"checkFilename(this)\"><br>\n");
		print("<span id=\"exists\"> (Existing file)</span>\n");
		print("<br><br>Page source:<br>\n");
		print("<textarea rows=\"40\" cols=\"120\" name=\"content\" form=\"editform\" onkeydown=\"insertTab(this, event);\">");
		print($contents);
		print("</textarea>\n");
		print("<br><br>Password (if you don't know it, just ask someone who does):<br>\n");
		print("	<input type=\"password\" name=\"password\"");
		if(isset($_SESSION['password']))
			print(" value=\"" . $_SESSION['password'] . "\"");
		print(">\n");
		print("<br><br><input type=\"submit\" value=\"Save\">\n");
		print("</form>\n");
		print("</body></html>\n");
	}
	else if(isset($_POST['content']))
	{
		if(isset($_POST['page']))
		{
			// Check the password
			if(!isset($_POST['password']) || $_POST['password'] != $password)
				die("Incorrect password");
			$_SESSION['password'] = $_POST['password'];

			// Check the path
			$pagename = htmlentities($_POST['page']);
			if(strlen($pagename) < 4 || substr($pagename, strlen($pagename) - 4, 4) != ".php")
				die("the page name must end with .php");
			$lastslash = strrpos($pagename, '/');
			if($lastslash !== FALSE || $pagename == "header.php" || $pagename == "footer.php")
				die("invalid pagename: " . $pagename);

			// Check for dangerous content
			if(stripos($_POST['content'], "<script") !== FALSE)
				die("Scripts are not allowed");
			$len = strlen($_POST['content']);
			$ofs = strpos($_POST['content'], "<?", $i);
			if($ofs !== FALSE)
			{
				$sub = substr($_POST['content'], $ofs, 30);
				die("Sorry, for security reasons, PHP code is not allowed. Only HTML is allowed. The offending snip is: " . htmlentities($sub));
			}

			// Save it
			$datestring = date('_Y-m-d_h-i-s_', time());
			rename($pagename, "history/" . $pagename . $datestring . $pagename);
			if(file_put_contents($pagename, $header . $_POST['content'] . $footer) === FALSE)
				die("Failed to write to file: " . $pagename);
			header('Location: ' . $pagename);
			print("<!doctype html><html><body>\n");
			print("Redirecting to <a href=\"" . $pagename . "\">" . $pagename . "</a>\n");
			print("</body></html>\n");
		}
		else
		{
			print("<!doctype html><html><body>\n");
			print("No page name<br>\n");
			print_r($_POST);
			print("</body></html>\n");
		}
	}
	else
	{
		print("<!doctype html><html><body>\n");
		print("what do you want?");
		print("</body></html>\n");
	}
?>
