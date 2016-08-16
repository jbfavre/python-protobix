-- MySQL dump 10.13  Distrib 5.6.30, for debian-linux-gnu (x86_64)
--
-- Host: 127.0.0.1    Database: zabbix
-- ------------------------------------------------------
-- Server version	5.5.5-10.1.16-MariaDB-1~jessie

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Dumping data for table `hosts`
--
-- WHERE:  hostid in (10105,10106)

LOCK TABLES `hosts` WRITE;
/*!40000 ALTER TABLE `hosts` DISABLE KEYS */;
INSERT INTO `hosts` VALUES (10105,NULL,'protobix.host1',0,0,'',0,0,0,-1,2,'','',0,0,0,0,NULL,0,0,0,0,0,'','',0,0,0,'','protobix.host1',0,NULL,'',1,1,'','','',''),(10106,NULL,'protobix.host2',0,0,'',0,0,0,-1,2,'','',0,0,0,0,NULL,0,0,0,0,0,'','',0,0,0,'','protobix.host2',0,NULL,'',1,7,'','','protobix','70726f746f62697870726f746f62697870726f746f62697870726f746f626978');
/*!40000 ALTER TABLE `hosts` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `items`
--
-- WHERE:  hostid in (10105,10106)

LOCK TABLES `items` WRITE;
/*!40000 ALTER TABLE `items` DISABLE KEYS */;
INSERT INTO `items` VALUES (23663,2,'','',10105,'my.protobix.item.int','my.protobix.item.int',0,1,1,0,3,'','',0,0,'',0,'','','1','',0,'',NULL,NULL,'','','',0,0,'','','','',0,0,NULL,'','',0,'30',0,0,0,'',0),(23664,2,'','',10105,'my.protobix.item.string','my.protobix.item.string',0,1,0,0,4,'','',0,0,'',0,'','','1','',0,'',NULL,NULL,'','','',0,0,'','','','',0,0,NULL,'','',0,'30',0,0,0,'',0),(23667,2,'','',10105,'my.protobix.lld_item1','my.protobix.lld_item1',0,90,0,0,4,'','',0,0,'',0,'','','','',0,'',NULL,NULL,'','','',0,0,'','','','',0,1,NULL,'','',0,'30',0,0,0,'',0),(23670,2,'','',10105,'my.protobix.lld_item2','my.protobix.lld_item2',0,90,0,0,4,'','',0,0,'',0,'','','','',0,'',NULL,NULL,'','','',0,0,'','','','',0,1,NULL,'','',0,'1',0,0,0,'',0),(23665,2,'','',10106,'my.protobix.item.int','my.protobix.item.int',0,1,1,0,3,'','',0,0,'',0,'','','1','',0,'',NULL,NULL,'','','',0,0,'','','','',0,0,NULL,'','',0,'30',0,0,0,'',0),(23666,2,'','',10106,'my.protobix.item.string','my.protobix.item.string',0,1,0,0,4,'','',0,0,'',0,'','','1','',0,'',NULL,NULL,'','','',0,0,'','','','',0,0,NULL,'','',0,'30',0,0,0,'',0),(23669,2,'','',10106,'my.protobix.lld_item1','my.protobix.lld_item1',0,90,0,0,4,'','',0,0,'',0,'','','','',0,'',NULL,NULL,'','','',0,0,'','','','',0,1,NULL,'','',0,'1',0,0,0,'',0),(23668,2,'','',10106,'my.protobix.lld_item2','my.protobix.lld_item2',0,90,0,0,4,'','',0,0,'',0,'','','','',0,'',NULL,NULL,'','','',0,0,'','','','',0,1,NULL,'','',0,'30',0,0,0,'',0);
/*!40000 ALTER TABLE `items` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2016-08-14  9:57:36
