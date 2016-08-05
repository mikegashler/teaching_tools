<!doctype html><html>
<head>
	<style>
		#content {
			margin-left:30px;
		}
		body {
			background-image:url('white_fade.png');
			background-color:#808080;
			background-repeat:repeat-x;
		}
	</style>

</head>
<body>
<?php
	// Figure out the name of this page
	$requestpath = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
	$lastslash = strrpos($requestpath, '/');
	if($lastslash === FALSE)
		$requestfile = $requestpath;
	else
		$requestfile = substr($requestpath, $lastslash + 1);
	if(strlen($requestfile) == 0)
		$requestfile = "index.php";
?>
<table align=center cellpadding=0 border=0 width=1000 bgcolor=#ffffff><tr><td>
<img src="banner.png"><br>
<table width=100%><tr><td align=left>
<?php
	print("<a href=\"index.php\">Home</a></td><td align=right><a href=\"edit.php?edit=" . $requestfile . "\">Edit page</a>");
?>
</td></tr></table>
<!--end of header-->



