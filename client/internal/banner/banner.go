package banner

import (
	"fmt"
)

const logo = `
┏┓┓     ┏┓   
┃┓┣┓┏┓┏╋┃┃┏┓┏
┗┛┛┗┗┛┛┗┗┛┣┛┛
          ┛  `

func Print() {
	fmt.Println(logo)
	fmt.Println()
}
