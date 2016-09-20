<?php

require_once('../mysqli_connect.php');

$timeNow = time();

parse_str($_SERVER["QUERY_STRING"]);


if ($userID != '1'){
	$query  = "UPDATE Devices set TimeCheckedOut = '{$timeNow}' where CheckedOutBy = '{$userID}'";
}

$response = @mysqli_query($dbc, $query);

if($response){
	
echo "Checkout(s) renewed for user ${userID}";
	
mysqli_close($dbc);

} else if ($userID == '1'){
	echo "Invalid User ID";

} else {
	
	echo "Couldn't issue database query";
	
	echo mysqli_error($dbc);
	
}
?>
