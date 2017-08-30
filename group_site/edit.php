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
<?php
		$pagename = htmlentities($_GET['edit']);
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
?>
<br><br><br><br><br><br><br><br><br><br>
<h3>Or upload and image</h3>
<form action="edit.php" method="post" id="uploadpic" enctype="multipart/form-data">
Choose an image to upload:
	<input type="hidden" name="upload_image" value="upload_image">
	<input type="file" name="fileToUpload" id="fileToUpload"><br>
	Password (if you don't know it, just ask someone who does):<br>
	<input type="password" name="password"><br>
	<input type="submit" name="submit" value="Upload Image">
</form>
<?php
		print("</body></html>\n");
	}
	else if(isset($_POST['content']))
	{
		if(isset($_POST['page']))
		{
			// Check the password
			if(!isset($_POST['password']) || $_POST['password'] != $password)
			{
				sleep(5); // Make it difficult to brute-force
				die("Incorrect password");
			}
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
	else if(isset($_POST['upload_image']))
	{
		// Check the password
		if(!isset($_POST['password']) || $_POST['password'] != $password)
		{
			sleep(5);
			die("Incorrect password");
		}

		$target_dir = "pics/";
		$target_file = $target_dir . basename($_FILES["fileToUpload"]["name"]);
		$uploadOk = 1;
		$imageFileType = pathinfo($target_file,PATHINFO_EXTENSION);
		
		// Check if image file is a actual image or fake image
		if(isset($_POST["submit"])) {
			$check = getimagesize($_FILES["fileToUpload"]["tmp_name"]);
			if($check !== false) {
				//echo "File is an image - " . $check["mime"] . ".";
				$uploadOk = 1;
			} else {
				echo "File is not an image.";
				$uploadOk = 0;
			}
		}
		
		// Check if file already exists
		if (file_exists($target_file)) {
			echo "Sorry, file already exists.";
			$uploadOk = 0;
		}
		
		// Check file size
		if ($_FILES["fileToUpload"]["size"] > 500000) {
			echo "Sorry, your file is too large.";
			$uploadOk = 0;
		}
		
		// Allow certain file formats
		if($imageFileType != "jpg" && $imageFileType != "png" && $imageFileType != "jpeg"
		&& $imageFileType != "gif" ) {
			echo "Sorry, only JPG, JPEG, PNG & GIF files are allowed.";
			$uploadOk = 0;
		}
		
		// Check if $uploadOk is set to 0 by an error
		if ($uploadOk == 0) {
			echo "Sorry, your file was not uploaded.";
			
		// if everything is ok, try to upload file
		} else {
			if (move_uploaded_file($_FILES["fileToUpload"]["tmp_name"], $target_file)) {
				echo "The file ". basename( $_FILES["fileToUpload"]["name"]). " has been uploaded.";
			} else {
				echo "Sorry, there was an error uploading your file.";
			}
		}
		
		
	}
	else
	{
		print("<!doctype html><html><body>\n");
		print("what do you want?");
		print("</body></html>\n");
	}
?>


