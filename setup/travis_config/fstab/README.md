* To generate UUID for a particular disk array.
  ```sh
  sudo blkid /dev/<disk-array>
  ```
* For optimal I/O performance on your XFS Filesystem, append the line in sample to the /etc/fstab file.
* In addition, this also automounts your disk array on the system.
* **IMPORTANT NOTE**: Do not add this line on an AWS instance with dedicated SSD's mainly the I/O optimized ones. Adding this line will cause problems as AWS reclaims the SSD's after the instance is shut-down.
