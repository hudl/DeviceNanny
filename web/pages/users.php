<html>
<head>
<title>Users List</title>
</head>
<body>

<p>
<?php

require_once('../mysqli_connect.php');

$query  = "SELECT UserID, FirstName, LastName, Office from Users WHERE (UserID != 0 AND UserID != 1) ORDER BY Office, FirstName";

$response = @mysqli_query($dbc, $query);

if($response){
	
	echo '<table align="left">
	
	<tr><td align="left"><b>User ID</b></td>
	<td align="left"><b>First Name</b></td>
	<td align="left"><b>Last Name</b></td>
	<td align="left"><b>Office</b></td></tr>';
	
	while($row = mysqli_fetch_array($response)){
		
		echo '<tr><td align="left">' .
		$row[UserID] . '</td><td align="left">' .
		$row[FirstName] . '</td><td align="left">' .
		$row[LastName] . '</td><td align="left">' .
		$row[Office] . '</td>';
		
		echo '</tr>';

	}
	
	echo '</table>';
	
} else {
	
	echo "Couldn't issue database query";
	
	echo mysqli_error($dbc);
	
}

mysqli_close($dbc)

?>

</p>
</body>
</html>
