<?php
	session_start();

	$base_path = "/home/mike/rs/paradigms/";
	$return_url = "http://uaf46365.ddns.uark.edu/paradigms/";
	$grader_name = "Phan,Hiep";
?>

<html>
<head>
	<style>
		.toc {
			margin-left: 30px;
		}
		.code {
			margin-left: 30px;
			color:#000000;
			background-color:#d0f0d0;
		}
		.shell {
			margin-left: 30px;
			color:#000000;
			background-color:#ffffff;
		}
	</style>
</head>
<script type="text/javascript">


var Sha256={};Sha256.hash=function(msg){msg=msg.utf8Encode();
var K=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
var H=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
msg+=String.fromCharCode(0x80);var l=msg.length/4+2;var N=Math.ceil(l/16);var M=new Array(N);
for(var i=0;i<N;i++){M[i]=new Array(16);for(var j=0;j<16;j++){
M[i][j]=(msg.charCodeAt(i*64+j*4)<<24)|(msg.charCodeAt(i*64+j*4+1)<<16)|
(msg.charCodeAt(i*64+j*4+2)<<8)|(msg.charCodeAt(i*64+j*4+3));}}
M[N-1][14]=((msg.length-1)*8) / Math.pow(2,32);M[N-1][14]=Math.floor(M[N-1][14]);
M[N-1][15]=((msg.length-1)*8)&0xffffffff;var W=new Array(64);var a,b,c,d,e,f,g,h;
for(var i=0;i<N;i++){for(var t=0;t<16;t++) W[t]=M[i][t];
for(var t=16;t<64;t++) W[t]=(Sha256.B1(W[t-2])+W[t-7]+Sha256.B0(W[t-15])+W[t-16])&0xffffffff;
a=H[0];b=H[1];c=H[2];d=H[3];e=H[4];f=H[5];g=H[6];h=H[7];for(var t=0;t<64;t++){
var T1=h+Sha256.A1(e)+Sha256.Ch(e,f,g)+K[t]+W[t];var T2=Sha256.A0(a)+Sha256.Maj(a,b,c);
h=g;g=f;f=e;e=(d+T1)&0xffffffff;d=c;c=b;b=a;a=(T1+T2)&0xffffffff;}
H[0]=(H[0]+a)&0xffffffff;H[1]=(H[1]+b)&0xffffffff;H[2]=(H[2]+c)&0xffffffff;H[3]=(H[3]+d)&0xffffffff;
H[4]=(H[4]+e)&0xffffffff;H[5]=(H[5]+f)&0xffffffff;H[6]=(H[6]+g)&0xffffffff;H[7]=(H[7]+h)&0xffffffff;}
return Sha256.toHex(H[0])+Sha256.toHex(H[1])+Sha256.toHex(H[2])+Sha256.toHex(H[3])+
Sha256.toHex(H[4])+Sha256.toHex(H[5])+Sha256.toHex(H[6])+Sha256.toHex(H[7]);};
Sha256.RO=function(n,x){return (x>>>n)|(x<<(32-n));};
Sha256.A0=function(x){return Sha256.RO(2, x)^Sha256.RO(13,x)^Sha256.RO(22,x);};
Sha256.A1=function(x){return Sha256.RO(6, x)^Sha256.RO(11,x)^Sha256.RO(25,x);};
Sha256.B0=function(x){return Sha256.RO(7, x)^Sha256.RO(18,x)^(x>>>3);};
Sha256.B1=function(x){return Sha256.RO(17,x)^Sha256.RO(19,x)^(x>>>10);};
Sha256.Ch=function(x,y,z){return (x&y)^(~x&z);};Sha256.Maj=function(x,y,z){return (x&y)^(x&z)^(y&z);};
Sha256.toHex=function(n){var s="",v;for(var i=7;i>=0;i--){v=(n>>>(i*4))&0xf;s+=v.toString(16);}
return s;};if(typeof String.prototype.utf8Encode=='undefined'){
String.prototype.utf8Encode=function(){return unescape(encodeURIComponent(this));};}
if(typeof String.prototype.utf8Decode=='undefined'){String.prototype.utf8Decode=function()
{try{return decodeURIComponent(escape(this));}catch(e){return this;}};}

<?php print("var salt=\"" . $salt . "\";\n"); ?>

function hashPasswordAndSubmit() {
	var rawPassword = document.forms["login"]["password"].value;
	var hashedPassword = Sha256.hash(salt + rawPassword);
	//alert(hashedPassword);
	document.forms["login"]["password"].value = hashedPassword;
	document.forms["login"].submit();
}

function hashNewPasswordAndSubmit() {
	var rawPassword = document.forms["change"]["changepassword"].value;
	var hashedPassword = Sha256.hash(salt + rawPassword);
	document.forms["change"]["changepassword"].value = hashedPassword;
	document.forms["change"].submit();
}

</script>

<body>

<?php
	// Process POST data
	$justcreatedaccount = false;
	if($_POST['logout'])
	{
		$_SESSION['realname'] = "";
		$_SESSION['password'] = "";
		$_SESSION['loggedin'] = false;
		print("You are logged out.<br><br>");
	}
	else if($_POST['login'])
	{
		// Verify the password
		$_SESSION['realname'] = "";
		$_SESSION['password'] = "";
		$_SESSION['loggedin'] = false;
		$accountsfile = fopen($base_path . "accounts.csv", 'r');
		$founduser = false;
		while($row = fgets($accountsfile))
		{
			$rowArray = explode(',', $row);
			$fullname = trim($rowArray[0]) . "," . trim($rowArray[1]);
			if(strcmp($fullname, $_POST['username']) == 0)
			{
				$founduser = true;
				$hashedEntry = trim($rowArray[2]);
				if(strcmp(trim($_POST['password']), $hashedEntry) == 0 || // Check against hashed entry in accounts.csv
					strcmp(trim($_POST['password']), hash('sha256', $salt . $hashedEntry)) == 0) // Check against unhashed entry in accounts.csv (using the PHP implementation of sha256)
				{
					// Log in
					$_SESSION['realname'] = $fullname;
					$_SESSION['password'] = trim($_POST['password']);
					$_SESSION['loggedin'] = true;
				}
				else
				{
					print("Incorrect password for " . $fullname . "<br><br>\n");
					if(strlen($_POST['username']) < 1)
						print("Someone has already changed the password for this account. If it was not you, then please notify the instructor immediately!<br><br>\n");
					else
						print("If you cannot remember your password, you can ask the instructor to reset it.<br><br>\n");
				}
			}
		}
		fclose($scoresdata);
		if(!$founduser)
			print("No record of user " . $_POST['username'] . "<br><br>\n");

		if($_SESSION['loggedin'] && strlen($_POST['changepassword']) > 0)
		{
			if(strpos($_POST['changepassword'], ",") === false)
			{
				if(strlen(trim($_POST['changepassword'])) > 0)
				{
					// Change the password
					$lockfile = fopen($base_path . "accounts.lock","w+");
					if(!flock($lockfile, LOCK_EX))
						die("Failed to acquire the lock. Your password was not changed! Please try again.");
					$accountsfile = fopen($base_path . "accounts.csv", 'r');
					$newaccountsfile = fopen($base_path . "newaccounts.csv", 'w');
					while($row = fgets($accountsfile))
					{
						$rowArray = explode(',', $row);
						$fullname = trim($rowArray[0]) . "," . trim($rowArray[1]);
						if(strcmp($fullname, $_POST['username']) == 0)
							fputs($newaccountsfile, trim($rowArray[0]) . "," . trim($rowArray[1]) . "," . trim($_POST['changepassword']) . "\n");
						else
							fputs($newaccountsfile, $row);
					}
					fclose($accountsfile);
					fclose($newaccountsfile);
					unlink($base_path . "oldaccounts.csv");
					rename($base_path . "accounts.csv", $base_path . "oldaccounts.csv");
					rename($base_path . "newaccounts.csv", $base_path . "accounts.csv");
					fclose($lockfile);
					$_SESSION['password'] = trim($_POST['changepassword']);
					print("Your password has been changed.<br><br>\n");
				}
				else
					print("Sorry, whitespace is not an acceptable password.<br><br>\n");
			}
			else
				print("Sorry, commas are not allowed in passwords.<br><br>\n");
		}
	}

	function col($i)
	{
		if($i < 26)
			return chr(97 + $i);
		$i -= 26;
		if($i < 26)
			return 'a' . chr(97 + $i);
		$i -= 26;
		if($i < 26)
			return 'b' . chr(97 + $i);
		$i -= 26;
		return 'c' . chr(97 + $i);
	}

	// Show the page content
	if(!$_SESSION['loggedin'])
	{
		// Show log-in form
		print("<a href=\"" . $return_url . "\">Return to class page</a><br><br>\n");
?>

		<h3>Log in to view your scores</h3>
		<form name="login" method="post" onsubmit="hashPasswordAndSubmit()">
		<input type="hidden" name="login" value="true">
		<table>
			<tr><td align="right">Name:</td><td><select name="username">
<?php
			$accountsfile = fopen($base_path . "accounts.csv", 'r');
			$founduser = false;
			while($row = fgets($accountsfile))
			{
				$rowArray = explode(',', $row);
				print("<option value=\"" . trim($rowArray[0]) . "," . trim($rowArray[1]) . "\">" . trim($rowArray[0]) . ", " . trim($rowArray[1]) . "</option>\n");
			}
			fclose($scoresdata);
?>
			</select></td></tr>

			<tr><td align="right">Password:</td><td><input type="password" name="password"></td></tr>
			<tr><td></td><td><input type="button" onclick="hashPasswordAndSubmit()" value="Log in"></td></tr>
		</table>
		</form><br><br>
<?php
	}
	else
	{
		// Show name and logout button
		print("Hello, " . $_SESSION['realname'] . ".<br>");
?>
		<form name="logout" method="post">
		<input type="hidden" name="logout" value="true">
		<input type="submit" name="logout" value="Log out">
		</form><br><br>

		<form name="change" method="post" onsubmit="hashNewPasswordAndSubmit()">
		<input type="hidden" name="login" value="true">
		<input type="hidden" name="username" value="<?php print($_SESSION['realname']);?>">
		<input type="hidden" name="password" value="<?php print($_SESSION['password']);?>">
		New Password:<input type="password" name="changepassword"><input type="button" onclick="hashNewPasswordAndSubmit()" value="Change password"><br>
		</form><br><br>
<?php
		// Force new users to change password
		if(strcmp($_SESSION['password'], hash('sha256', $salt)) == 0)
			die("You cannot view your scores until you change your password.");

		// Show scores
		$ss = "";
		print("<table border=1>\n");
		$linenum = 1;
		$printline = 1;
		$scoresdata = fopen($base_path . "scores.csv", 'r');
		$founduser = false;
		$weightcols = 0;
		while($row = fgets($scoresdata))
		{
			// Determine what the logged-in user is authorized to view
			$rowArray = explode(',', $row);
			$studentname = trim($rowArray[0]) . "," . trim($rowArray[1]);
			$showline = false;
			if($linenum < 4)
				$showline = true;
			else if($_SESSION['realname'] == "Gashler,Michael S") {
				$showline = true;
				$founduser = true;
			}
			else if($_SESSION['realname'] == $grader_name) {
				$showline = true;
				$founduser = true;
			}
			else if($_SESSION['realname'] == $studentname) {
				$showline = true;
				$founduser = true;
			}

			// Show the line if the logged-in user is authorized to view this student's score
			if($showline) {
				$col = 0;
				print("<tr>");

				// Display all the scores
				foreach($rowArray as $el) {
					print("<td>");
					print(trim($el));
					$ss = $ss . trim($el) . "\t"; // add them to the spreadsheet version too
					print("</td>");
					$col++;
				}

				// Add the row-end formulas to the spread sheet
				if($linenum == 1)
					$formula = "Weighted total\tPercent";
				else if($linenum == 2)
					$formula = "";
				else
					$formula = "=";
				if($linenum == 3) { // If this is the "weights" line...
					$weightcols = $col;
					for($i = 2; $i < $weightcols; $i++) {
						if($i > 2)
							$formula = $formula . "+";
						$formula = $formula . col($i) . "3";
					}
				}
				else if($linenum > 3) { // If this is a "student scores" line...
					// Produce the formula string
					for($i = 2; $i < $weightcols; $i++) {
						if($i > 2)
							$formula = $formula . "+";
						$formula = $formula . "if(" . col($i) . "$3>0," . col($i) . $printline . "/" . col($i) . "$2*" . col($i) . "$3,0)";
					}

					// Tab out to the second-to-last column
					while($col < $weightcols)
					{
						$formula = "\t" . $formula;
						$col++;
					}

					// Add a final formula cell to calculate the score
					$formula = $formula . "\t=" . col($col) . $printline . "/" . col($col) . "$3";
				}
				$ss = $ss . $formula . "\n";
				print("</tr>\n");
				$printline++;
			}
			$linenum++;
		}

		// Add Median and average lines to the spreadsheet
		if($printline > 5)
		{
			$ss = $ss . "	Median";
			for($i = 0; $i < $weightcols; $i++)
				$ss = $ss . "	=median(" . col(2 + $i) . "4:" . col(2 + $i) . ($linenum - 1) . ")";
			$ss = $ss . "\n";
			$ss = $ss . "	Average";
			for($i = 0; $i < $weightcols; $i++)
				$ss = $ss . "	=average(" . col(2 + $i) . "4:" . col(2 + $i) . ($linenum - 1) . ")";
			$ss = $ss . "\n";
		}

		fclose($scoresdata);
		print("</table><br>");
		if(!$founduser)
			print("<big><big><big>No scores have yet been entered for " . $_SESSION['realname'] . ". If you should have scores, please contact the instructor.</big></big></big>");
		print("<br><br><br><br><h3>Spreadsheet-friendly version:</h3>\n");
		print("<p>Instructions:<ol><li>Copy the text below (ctrl-C).</li><li>Open LibreOffice spreadsheet and paste into cell A1. (Use only tabs as separators. Do not let commas be separators.)</li><li>To see your current score, set the weight of any assignments you have not yet submitted to 0.</li></ol>\n");
		print("<font size=0><small><small><textarea onfocus=\"this.select()\" readonly=\"readonly\" autofocus rows=10 cols=100 class=\"code\">\n" . $ss . "</textarea></small></small></font>");
	}
?>
<br><br><br><br><br><br><br><br>
</body>
</html>
