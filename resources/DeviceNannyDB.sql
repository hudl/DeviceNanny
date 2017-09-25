SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `DeviceNanny`
--

-- --------------------------------------------------------

--
-- Table structure for table `Devices`
--

CREATE TABLE IF NOT EXISTS `Devices` (
  `DeviceID` int(11) NOT NULL,
  `DeviceName` text NOT NULL,
  `SerialUDID` text NOT NULL,
  `Manufacturer` text NOT NULL,
  `Model` text NOT NULL,
  `Type` text NOT NULL,
  `OS` text NOT NULL,
  `CheckedOutBy` int(11) DEFAULT '0',
  `TimeCheckedOut` int(11) DEFAULT '0',
  `LastReminded` int(11) DEFAULT '0',
  `Location` text NOT NULL,
  `Port` text
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Table structure for table `Users`
--

CREATE TABLE IF NOT EXISTS `Users` (
  `UserID` int(11) NOT NULL,
  `FirstName` text NOT NULL,
  `LastName` text NOT NULL,
  `SlackID` text NOT NULL,
  `Office` text
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Dumping data for table `Users`
--

INSERT INTO `Users` (`UserID`, `FirstName`, `LastName`, `SlackID`, `Office`) VALUES
(0, '-', '-', '', ''),
(1, 'Missing', 'Device', '', '');

--
-- Indexes for table `Devices`
--
ALTER TABLE `Devices`
 ADD PRIMARY KEY (`DeviceID`);

--
-- Indexes for table `Users`
--
ALTER TABLE `Users`
 ADD PRIMARY KEY (`UserID`);
--