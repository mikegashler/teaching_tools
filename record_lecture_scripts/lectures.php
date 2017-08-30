<?php
	$file_path = "/var/www/html/advai/";
	$web_path = "http://uaf56986.ddns.uark.edu/advai/";
	$return_url = "http://csce.uark.edu/~mgashler/advai/";
	$lock_date = "2017-07-26";
?>

<html>
<head>
	<style>
		body {
			background-image:url('black_fade.png');
			background-color:#60a0a0;
			background-repeat:repeat-x;
		}
		.code {
			margin-left: 30px;
			color:#000000;
			background-color:#ffffff;
		}
	</style>
</head>

<body>
<br><br>
<table align=center cellpadding=50 border=1 bgcolor=#f0f0f0 width=720><tr><td>

<h1>Advanced Artificial Intelligence Lectures</h1>

<?php
	function annotation_comparer($a, $b)
	{
		$v = strcmp($a->video, $b->video);
		if($v < 0)
			return -1;
		else if($v > 0)
			return 1;
		else if(intval($a->time) < intval($b->time))
			return -1;
		else if(intval($a->time) > intval($b->time))
			return 1;
		else
			return 0;
	}


	$raw = file_get_contents("annotations/annotations.json");
	if($raw === FALSE)
		$annotations = array();
	else
		$annotations = json_decode($raw);

	if($_GET['video'] && $_GET['time'])
	{
		$new_ann = new stdClass();
		$new_ann->video = $_GET['video'];
		$new_ann->time = $_GET['time'];
		if($_GET['descr'])
			$new_ann->descr = $_GET['descr'];
		else
			$new_ann->descr = "";
		if(strcmp($new_ann->video, $lock_date) <= 0)
			print("Annotations before " . $lock_date . " are currently locked.");
		else if(strstr($new_ann->time, ":") === FALSE)
			print("Expected a : in the timestamp.");
		else if($new_ann->descr !== htmlentities($new_ann->descr))
			print("HTML entities are not allowed.");
		else if(strstr($new_ann->descr, ".com") !== FALSE)
			print(".com is not allowed in the description.");
		else if(strstr($new_ann->descr, ":") !== FALSE)
			print(": is not allowed in the description.");
		else if(strstr($new_ann->descr, "!") !== FALSE)
			print("! is not allowed in the description.");
		else if(strstr($new_ann->descr, "*") !== FALSE)
			print("* is not allowed in the description.");
		else
		{
			// Keep all the annotations except for any that match the new video and time stamp.
			$new_annotations = array();
			for($i = 0; $i < sizeof($annotations); $i++)
			{
				if($annotations[$i]->video !== $new_ann->video || $annotations[$i]->time !== $new_ann->time)
					$new_annotations []= $annotations[$i];
			}
			$annotations = $new_annotations;

			// Add the new annotation to the array
			if(strlen($new_ann->descr) > 0)
				$annotations []= $new_ann;

			// Save to disk
			$fh = fopen("annotations/annotations.json", 'w');
			if($fh === false)
				die("Failed to open annotations.json for writing.");
			else
			{
				fwrite($fh, json_encode($annotations));
				fclose($fh);
			}
		}
	}

	// Sort the annotations
	usort($annotations, "annotation_comparer");

	//$files = scandir($video_path);
	$files = glob($file_path . "*.*");
	$small_videos = array();
	$big_videos = array();
	for($i = 0; $i < sizeof($files); $i++) // for each file...
	{
		$parts = pathinfo($files[$i]);
		if($parts['extension'] === "ogv" || $parts['extension'] === "mp4" || $parts['extension'] === "MTS") // if it looks like a video...
		{
			if(substr($parts['basename'], 0, 5) === "small")
				$small_videos []= $parts['basename'];
			else
				$big_videos []= $parts['basename'];
		}
	}

	print("<table>");
	$prevYear = "";
	for($i = 0; $i < sizeof($small_videos); $i++) // for each small video...
	{
		// Low resolution video
		$display_name = substr($small_videos[$i], 5);
		$year = substr($display_name, 0, 4);
		if(strcmp($year, $prevYear) != 0)
		{
			print("<br><br><br><br><br><br><a id=\"" . $year . "\">");
			print("<tr><td><h1>" . $year . "</h1></td></tr>\n");
			print("<tr><td><b><u>Low resolution</u></b></td><td><b><u>High resolution</u></b></td><td><b><u>Annotations</u></b></td></tr>\n");
			$prevYear = $year;
		}
		
		print("<tr>");
		print("<td valign=top><a href=\"" . $web_path . $small_videos[$i] . "\" target=\"_blank\">" . $display_name . "</a></td>");

		// High resolution video
		$high_res_index = array_search($display_name, $big_videos);
		if($high_res_index === FALSE)
			print("<td></td>");
		else
			print("<td valign=top><a href=\"" . $web_path . $big_videos[$high_res_index] . "\" target=\"_blank\">" . $display_name . "</a></td>");
		print("<td>\n");

		// Table of annotations
		
		print("<table>\n");
		for($j = 0; $j < sizeof($annotations); $j++)
		{
			$ann = $annotations[$j];
			if($ann->video === $display_name)
			{
				print("<tr><td>" . $ann->time . "</td><td>" . $ann->descr . "</td></tr>\n");
			}
		}
		print("</table>\n");

		// Form to add new annotations
		if(strcmp($display_name, $lock_date) > 0)
		{
			print("<form>");
			print("<input type=\"hidden\" name=\"video\" value=\"" . $display_name . "\">");
			print("<input type=\"text\" name=\"time\" size=\"3\">");
			print("<input type=\"text\" name=\"descr\" size=\"25\">");
			print("<input type=\"submit\" value=\"Add\">");
			print("</form>");
		}
		print("</td>\n</tr>\n\n");
	}
	print("</table>\n");
?>
<br><br>
To add an annotation, enter a timestamp and description, then press "Add".<br>
To remove one, just enter the timestamp, and press "Add".<br><br>
</td></tr></table><br><br><br>
</body></html>

